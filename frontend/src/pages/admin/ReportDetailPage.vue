<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElDescriptions, ElDescriptionsItem, ElDialog, ElForm, ElFormItem, ElInput, ElMessage, ElMessageBox, ElTimeline, ElTimelineItem } from "element-plus";
import { ApiError } from "@/api/http";
import { reportsApi, STATUS_LABEL } from "@/api/reports";
import type { AdminReportDetail } from "@/types/report";
import { useAuthStore } from "@/stores/auth";
import { AppButton, AppCard, AppEmpty, AppPageHeader, AppSkeleton, AppStatusTag } from "@/components";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const loading = ref(false);
const detail = ref<AdminReportDetail | null>(null);
const viewerUrl = ref<string | null>(null);
const viewerTitle = ref("");
const contactInfo = ref<{ phone?: string | null; email?: string | null } | null>(null);
const contactDialogVisible = ref(false);
const viewerVisible = ref(false);

const dialogMode = ref<"resolve" | "reject" | "transfer" | null>(null);
const actionDialogVisible = computed<boolean>({
  get: () => dialogMode.value !== null,
  set: (value) => {
    if (!value) dialogMode.value = null;
  },
});
const actionLoading = ref(false);

const resolveForm = reactive({
  desensitized_summary: "",
  identification_points: "",
  prevention_advice: "",
  internal_remark: "",
});

const rejectForm = reactive({
  reason: "",
  internal_remark: "",
});

const transferForm = reactive({
  transfer_note: "",
  internal_remark: "",
});

const caseId = computed<string>(() => {
  const raw = route.params.case_id;
  return typeof raw === "string" ? raw : Array.isArray(raw) ? raw[0] ?? "" : "";
});
const canReview = computed<boolean>(() => detail.value?.status === "REVIEWING");
const canDecryptAnonymous = computed<boolean>(() => auth.hasRole("SYS_ADMIN") && !!detail.value?.is_anonymous);

function statusTone(status: string): "neutral" | "info" | "success" | "danger" | "warning" {
  if (status === "PENDING") return "neutral";
  if (status === "REVIEWING") return "info";
  if (status === "HANDLED") return "success";
  if (status === "REJECTED") return "danger";
  return "warning";
}

async function load(): Promise<void> {
  loading.value = true;
  try {
    if (!/^\d+$/.test(caseId.value)) {
      throw new Error("invalid-case-id");
    }
    detail.value = await reportsApi.getAdminReport(caseId.value);
  } catch (error) {
    if (error instanceof ApiError && error.httpStatus === 409) {
      ElMessage.warning("该事件已被其他管理员处理，请刷新页面");
    }
  } finally {
    loading.value = false;
  }
}

async function openEvidence(fileId: string, fileName: string): Promise<void> {
  await ElMessageBox.confirm(
    "查看证据图片将被完整记录至审计日志。请确认您正在执行合规审核工作。",
    "敏感操作确认",
    { confirmButtonText: "确认查看", cancelButtonText: "取消", type: "warning" },
  );
  const blob = await reportsApi.viewEvidence(caseId.value, fileId);
  const url = URL.createObjectURL(blob);
  if (!blob.type.startsWith("image/")) {
    window.open(url, "_blank", "noopener");
    return;
  }
  viewerTitle.value = fileName;
  viewerUrl.value = url;
  viewerVisible.value = true;
}

async function handleContactReporter(): Promise<void> {
  if (!detail.value) return;
  if (detail.value.is_anonymous) {
    await ElMessageBox.alert(
      "匿名上报者联系方式不可见，如确需联系，请通过系统管理员申请司法协助查询流程。",
      "无法查看",
      { type: "warning" },
    );
    return;
  }
  await ElMessageBox.confirm(
    "查看联系方式将被记录至审计日志，是否继续？",
    "敏感操作确认",
    { confirmButtonText: "继续查看", cancelButtonText: "取消", type: "warning" },
  );
  contactInfo.value = await reportsApi.requestContactInfo(caseId.value);
  contactDialogVisible.value = true;
}

function closeViewer(): void {
  if (viewerUrl.value) URL.revokeObjectURL(viewerUrl.value);
  viewerUrl.value = null;
  viewerVisible.value = false;
}

function openDialog(mode: "resolve" | "reject" | "transfer"): void {
  dialogMode.value = mode;
}

async function submitAction(): Promise<void> {
  if (!detail.value) return;
  actionLoading.value = true;
  try {
    if (dialogMode.value === "resolve") {
      await reportsApi.resolveAdminReport(caseId.value, resolveForm);
      ElMessage.success("已录入案例库并标记为已处理");
    } else if (dialogMode.value === "reject") {
      await reportsApi.rejectAdminReport(caseId.value, rejectForm);
      ElMessage.success("已驳回该上报");
    } else if (dialogMode.value === "transfer") {
      await reportsApi.transferAdminReport(caseId.value, transferForm);
      ElMessage.success("已标记为转报警");
    }
    actionDialogVisible.value = false;
    await load();
  } catch (error) {
    if (error instanceof ApiError && error.httpStatus === 409) {
      ElMessage.warning("该事件已被其他管理员处理，请刷新页面");
    } else if (error instanceof ApiError && error.httpStatus === 422) {
      ElMessage.error(error.message || "请检查必填内容是否已填写");
    } else if (error instanceof ApiError) {
      ElMessage.error(error.message || "提交失败，请稍后重试");
    } else {
      ElMessage.error("提交失败，请稍后重试");
    }
  } finally {
    actionLoading.value = false;
  }
}

async function handleDecryptAnonymous(): Promise<void> {
  const { value } = await ElMessageBox.prompt(
    "请填写解密原因，该操作会通知所有系统管理员。",
    "匿名身份解密",
    {
      confirmButtonText: "确认解密",
      cancelButtonText: "取消",
      inputType: "textarea",
      inputValidator: (text) => text.trim().length >= 1,
      inputErrorMessage: "请输入解密原因",
    },
  );
  const result = await reportsApi.decryptAnonymous(caseId.value, {
    reason: value,
    ...(auth.me?.user_id ? { approver_id: auth.me.user_id } : {}),
  });
  await ElMessageBox.alert(
    `姓名：${result.real_name}\n账号：${result.cas_account}\n电话：${result.phone || "—"}\n邮箱：${result.email || "—"}`,
    "匿名身份已解密",
    { type: "warning" },
  );
}

onMounted(load);
onBeforeUnmount(closeViewer);
</script>

<template>
  <div class="admin-report-detail">
    <AppPageHeader v-if="detail" badge="UC-06" :title="detail.case_no" subtitle="审核详情与处理动作">
      <template #actions>
        <AppStatusTag :status="statusTone(detail.status)" :text="STATUS_LABEL[detail.status] || detail.status" />
      </template>
    </AppPageHeader>

    <div v-if="loading" class="admin-report-detail__loading">
      <AppSkeleton />
    </div>
    <div v-else-if="!detail" class="admin-report-detail__empty">
      <AppEmpty title="案件不存在" hint="请返回列表重试。" illustration="warning">
        <template #action>
          <AppButton variant="primary" @click="router.push({ name: 'admin-reports' })">返回列表</AppButton>
        </template>
      </AppEmpty>
    </div>
    <template v-else>
      <section class="admin-report-detail__grid">
        <AppCard padding="md">
          <template #header>
            <div>
              <h3>基本信息</h3>
              <small>当前审核员：{{ detail.reviewer?.real_name || "未分配" }}</small>
            </div>
          </template>
          <ElDescriptions :column="2" border>
            <ElDescriptionsItem label="诈骗类型">{{ detail.fraud_type_name || "—" }}</ElDescriptionsItem>
            <ElDescriptionsItem label="金额">{{ detail.amount ?? "—" }}</ElDescriptionsItem>
            <ElDescriptionsItem label="事发日期">{{ detail.incident_date }}</ElDescriptionsItem>
            <ElDescriptionsItem label="院系">{{ detail.dept_code }}</ElDescriptionsItem>
            <ElDescriptionsItem label="联系方式">{{ detail.contact_way || "—" }}</ElDescriptionsItem>
            <ElDescriptionsItem label="状态">{{ STATUS_LABEL[detail.status] || detail.status }}</ElDescriptionsItem>
          </ElDescriptions>
          <div class="block">
            <h4>事件经过</h4>
            <p>{{ detail.description }}</p>
          </div>
          <div class="block">
            <h4>处理时间线</h4>
            <ElTimeline>
              <ElTimelineItem v-for="item in detail.history" :key="item.history_id" :timestamp="item.created_at.slice(0, 16).replace('T', ' ')" :type="item.to_status === 'HANDLED' ? 'success' : item.to_status === 'REJECTED' ? 'danger' : item.to_status === 'REPORTED' ? 'warning' : 'primary'">
                {{ STATUS_LABEL[item.to_status] || item.to_status }}<span v-if="item.note">：{{ item.note }}</span>
              </ElTimelineItem>
            </ElTimeline>
          </div>
        </AppCard>

        <div class="admin-report-detail__side">
          <AppCard padding="md">
            <template #header>
              <div>
                <h3>证据材料</h3>
                <small>{{ detail.evidence_list.length }} 份证据</small>
              </div>
            </template>
            <div v-if="detail.evidence_list.length" class="evidence-list">
              <button v-for="item in detail.evidence_list" :key="item.file_id" type="button" class="evidence-item" @click="openEvidence(item.file_id, item.original_name)">
                <strong>{{ item.original_name }}</strong>
                <small>{{ item.mime_type }} · {{ item.file_size }} B</small>
              </button>
            </div>
            <AppEmpty v-else title="暂无证据" hint="该案件尚未上传证据文件。" />
          </AppCard>

          <AppCard padding="md">
            <template #header>
              <div>
                <h3>上报者信息</h3>
                <small>{{ detail.is_anonymous ? "匿名上报" : "实名上报" }}</small>
              </div>
            </template>
            <div v-if="detail.reporter" class="reporter-card">
              <p>姓名：{{ detail.reporter.real_name }}</p>
              <p>账号：{{ detail.reporter.cas_account }}</p>
            </div>
            <AppEmpty v-else title="匿名上报" hint="已对上报者身份信息做隔离保护。" />
            <div class="action-row">
              <AppButton variant="ghost" @click="handleContactReporter">联系上报人</AppButton>
              <AppButton v-if="canDecryptAnonymous" variant="danger" @click="handleDecryptAnonymous">解密匿名身份</AppButton>
            </div>
          </AppCard>
        </div>
      </section>

      <AppCard padding="md">
        <template #header>
          <div>
            <h3>处理动作</h3>
            <small>仅审核中状态可执行</small>
          </div>
        </template>
        <div v-if="canReview" class="action-row">
          <AppButton variant="primary" @click="openDialog('resolve')">录入案例库</AppButton>
          <AppButton variant="ghost" @click="openDialog('reject')">驳回</AppButton>
          <AppButton variant="danger" @click="openDialog('transfer')">标记转报警</AppButton>
        </div>
        <AppEmpty v-else title="当前状态不可处理" hint="只有审核中的案件才显示处理动作。" />
      </AppCard>
    </template>

    <ElDialog v-model="contactDialogVisible" title="联系方式" width="420px">
      <div class="contact-dialog">
        <p>电话：{{ contactInfo?.phone || "—" }}</p>
        <p>邮箱：{{ contactInfo?.email || "—" }}</p>
      </div>
    </ElDialog>

    <ElDialog v-model="viewerVisible" :title="viewerTitle" width="70%" @closed="closeViewer">
      <img v-if="viewerUrl" :src="viewerUrl" alt="证据图片" class="evidence-preview" />
    </ElDialog>

    <ElDialog v-model="actionDialogVisible" :title="dialogMode === 'resolve' ? '录入知识库案例' : dialogMode === 'reject' ? '驳回上报' : '标记转报警'" width="680px">
      <ElForm v-if="dialogMode === 'resolve'" label-position="top">
        <ElFormItem label="脱敏案例摘要" required>
          <ElInput
            v-model="resolveForm.desensitized_summary"
            type="textarea"
            :rows="4"
            placeholder="填写脱敏后的案例摘要"
          />
        </ElFormItem>
        <ElFormItem label="识别要点" required>
          <ElInput
            v-model="resolveForm.identification_points"
            type="textarea"
            :rows="3"
            placeholder="填写学生可识别的风险要点"
          />
        </ElFormItem>
        <ElFormItem label="防范建议" required>
          <ElInput
            v-model="resolveForm.prevention_advice"
            type="textarea"
            :rows="3"
            placeholder="填写可执行的防范建议"
          />
        </ElFormItem>
        <ElFormItem label="内部备注">
          <ElInput
            v-model="resolveForm.internal_remark"
            type="textarea"
            :rows="2"
            placeholder="填写内部备注（可选）"
          />
        </ElFormItem>
      </ElForm>
      <ElForm v-else-if="dialogMode === 'reject'" label-position="top">
        <ElFormItem label="驳回原因" required>
          <ElInput
            v-model="rejectForm.reason"
            type="textarea"
            :rows="4"
            placeholder="填写驳回原因"
          />
        </ElFormItem>
        <ElFormItem label="内部备注">
          <ElInput
            v-model="rejectForm.internal_remark"
            type="textarea"
            :rows="2"
            placeholder="填写内部备注（可选）"
          />
        </ElFormItem>
      </ElForm>
      <ElForm v-else-if="dialogMode === 'transfer'" label-position="top">
        <ElFormItem label="转报说明" required>
          <ElInput
            v-model="transferForm.transfer_note"
            type="textarea"
            :rows="4"
            placeholder="填写转报警说明"
          />
        </ElFormItem>
        <ElFormItem label="内部备注">
          <ElInput
            v-model="transferForm.internal_remark"
            type="textarea"
            :rows="2"
            placeholder="填写内部备注（可选）"
          />
        </ElFormItem>
      </ElForm>
      <template #footer>
        <AppButton variant="ghost" @click="actionDialogVisible = false">取消</AppButton>
        <AppButton variant="primary" :loading="actionLoading" @click="submitAction">确认提交</AppButton>
      </template>
    </ElDialog>
  </div>
</template>

<style scoped>
.admin-report-detail {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.admin-report-detail__grid {
  display: grid;
  grid-template-columns: minmax(0, 3fr) minmax(320px, 2fr);
  gap: var(--space-4);
}

.admin-report-detail__side {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.admin-report-detail__loading,
.admin-report-detail__empty {
  min-height: 360px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.block {
  margin-top: var(--space-4);
}

.block h4 {
  margin: 0 0 var(--space-2);
  font-size: var(--font-size-sm);
}

.block p {
  margin: 0;
  line-height: 1.8;
  color: var(--color-text-secondary);
}

.evidence-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.evidence-item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  padding: var(--space-3);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-bg-soft);
  cursor: pointer;
}

.evidence-item strong {
  color: var(--color-text-strong);
}

.evidence-item small,
.reporter-card p,
.contact-dialog p {
  color: var(--color-text-secondary);
  margin: 0;
}

.action-row {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
  margin-top: var(--space-3);
}

.evidence-preview {
  width: 100%;
  max-height: 70vh;
  object-fit: contain;
}

@media (width <= 1024px) {
  .admin-report-detail__grid {
    grid-template-columns: 1fr;
  }
}
</style>
