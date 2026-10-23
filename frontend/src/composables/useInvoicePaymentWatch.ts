import { computed, onBeforeUnmount, ref } from "vue";
import { syncBillingInvoice, type BillingInvoice } from "../services/billing";
import { useAuthStore } from "../store/useAuthStore";

const CHECK_EVERY_MS = 15_000;
const GIVE_UP_AFTER_MS = 10 * 60_000;

/**
 * Depois que a pessoa abre a fatura para pagar, confere o pagamento no Asaas a cada 15 s por até
 * 10 min (e de novo quando ela volta para a aba). Ao reconhecer o pagamento, recarrega o usuário
 * para a conta sair do bloqueio sem ela sair do painel.
 */
export function useInvoicePaymentWatch(onPaid?: (invoice: BillingInvoice) => void | Promise<void>) {
  const auth = useAuthStore();
  const invoiceId = ref<string | null>(null);
  const phase = ref<"idle" | "checking" | "paid" | "gave-up">("idle");
  const checking = ref(false);
  const hint = ref("");
  let timer: ReturnType<typeof setInterval> | null = null;
  let startedAt = 0;

  const watching = computed(() => phase.value === "checking");

  const stopTimer = () => {
    if (timer) clearInterval(timer);
    timer = null;
    document.removeEventListener("visibilitychange", onVisible);
  };

  const checkNow = async () => {
    if (!invoiceId.value || checking.value) return;
    checking.value = true;
    hint.value = "";
    try {
      const result = await syncBillingInvoice(invoiceId.value);
      if (result.paid) {
        stopTimer();
        phase.value = "paid";
        try {
          await auth.fetchProfile();
        } catch (err) {
          console.error("Erro ao recarregar o usuário depois do pagamento", err);
        }
        await onPaid?.(result.invoice);
        return;
      }
      hint.value = "Ainda não recebemos o pagamento.";
    } catch (err: any) {
      if (err?.response?.status === 429) {
        hint.value = "Aguarde alguns segundos para conferir de novo.";
      } else {
        console.error("Erro ao conferir o pagamento", err);
        hint.value = "Não foi possível conferir agora. Tentamos de novo em instantes.";
      }
    } finally {
      checking.value = false;
    }
  };

  function onVisible() {
    if (document.visibilityState === "visible") void checkNow();
  }

  const start = (id: string) => {
    stopTimer();
    invoiceId.value = id;
    phase.value = "checking";
    hint.value = "";
    startedAt = Date.now();
    timer = setInterval(() => {
      if (Date.now() - startedAt > GIVE_UP_AFTER_MS) {
        stopTimer();
        phase.value = "gave-up";
        return;
      }
      void checkNow();
    }, CHECK_EVERY_MS);
    document.addEventListener("visibilitychange", onVisible);
  };

  const reset = () => {
    stopTimer();
    invoiceId.value = null;
    phase.value = "idle";
    hint.value = "";
  };

  onBeforeUnmount(stopTimer);

  return { invoiceId, phase, watching, checking, hint, start, checkNow, reset };
}
