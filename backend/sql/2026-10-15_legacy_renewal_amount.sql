-- Renovação dos planos antigos (Profissional, Agência e Escala) pelo mesmo valor que o cliente pagava.
--
-- Rodar À MÃO no Postgres de produção ANTES de subir o código novo. Pode rodar mais de uma vez:
-- a coluna é criada só se não existir e o UPDATE só preenche quem ainda está sem valor.
-- Esta mudança NÃO tem revisão do alembic: o deploy não roda o alembic (o schema é mantido por
-- create_all e pelos ALTER ... IF NOT EXISTS em backend/app/main.py, que também cria esta coluna).
--
-- Regra (decidida pelo dono do produto):
--   * Só assinaturas com provider asaas ou cakto, plano professional, essencial, agency, growth,
--     scale ou infinity (nunca teste) e criadas antes do corte: 15/10/2026 00:00 em Brasília
--     (o plano único começou a ser vendido em 14/10/2026). Inclui as inativas (clientes que voltam).
--   * Asaas: vale o pagamento MAIS RECENTE entre (a) o último PAYMENT_CONFIRMED/PAYMENT_RECEIVED
--     de asaas_event_logs da assinatura Asaas atual (payment.value; data = payment.paymentDate ou o
--     dia do evento) e (b) a última compra paga no checkout do mesmo usuário (checkout_sessions.amount;
--     data = paid_at). Empate no mesmo dia: vale a compra do checkout (é o valor cheio da recorrência).
--     Sem nenhum dos dois: mrr_amount, se > 0 e o ciclo for mensal.
--   * Cakto: não há pagamento Asaas; vale mrr_amount, se > 0 e o ciclo for mensal.
--   * Só contam pagamentos anteriores ao corte. Quem pagou alguma compra no checkout depois do corte
--     fica de fora (já comprou uma oferta atual). Valores abaixo de R$ 10,00 (compras de teste) ficam
--     de fora.
--   * O valor é o do CICLO: mensal = valor do mês; anual = valor do ano.

BEGIN;

ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS legacy_renewal_amount NUMERIC(12, 2);

WITH asaas_payments AS (
    SELECT
        s.id AS subscription_id,
        CASE
            WHEN (l.payload -> 'payment' ->> 'value') ~ '^[0-9]+(\.[0-9]+)?$'
                THEN CAST(l.payload -> 'payment' ->> 'value' AS NUMERIC(12, 2))
        END AS amount,
        CASE
            WHEN (l.payload -> 'payment' ->> 'paymentDate') ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}'
                THEN CAST(LEFT(l.payload -> 'payment' ->> 'paymentDate', 10) AS DATE)
            ELSE CAST(l.created_at AT TIME ZONE 'America/Sao_Paulo' AS DATE)
        END AS paid_on,
        0 AS source_rank,
        l.created_at AS paid_ts
    FROM subscriptions s
    JOIN asaas_event_logs l
        ON (l.payload -> 'payment' ->> 'subscription') = s.asaas_subscription_id
    WHERE LOWER(s.provider) = 'asaas'
      AND s.asaas_subscription_id IS NOT NULL
      AND l.event_type IN ('PAYMENT_CONFIRMED', 'PAYMENT_RECEIVED')
),
checkout_purchases AS (
    SELECT
        s.id AS subscription_id,
        CAST(cs.amount AS NUMERIC(12, 2)) AS amount,
        CAST(cs.paid_at AT TIME ZONE 'America/Sao_Paulo' AS DATE) AS paid_on,
        1 AS source_rank,
        cs.paid_at AS paid_ts
    FROM subscriptions s
    JOIN checkout_sessions cs ON cs.user_id = s.user_id
    WHERE LOWER(s.provider) = 'asaas'
      AND cs.paid_at IS NOT NULL
      AND LOWER(COALESCE(cs.plan_key, '')) NOT IN ('test', 'teste')
),
latest_payment AS (
    SELECT DISTINCT ON (evidence.subscription_id)
        evidence.subscription_id,
        evidence.amount
    FROM (
        SELECT * FROM asaas_payments
        UNION ALL
        SELECT * FROM checkout_purchases
    ) AS evidence
    WHERE evidence.amount IS NOT NULL
      AND evidence.paid_on < DATE '2026-10-15'
    ORDER BY evidence.subscription_id, evidence.paid_on DESC, evidence.source_rank DESC, evidence.paid_ts DESC
),
candidates AS (
    SELECT
        s.id AS subscription_id,
        CASE
            WHEN LOWER(s.provider) = 'asaas' THEN COALESCE(
                lp.amount,
                CASE WHEN s.billing_cycle = 'monthly' AND s.mrr_amount > 0 THEN s.mrr_amount END
            )
            ELSE CASE WHEN s.billing_cycle = 'monthly' AND s.mrr_amount > 0 THEN s.mrr_amount END
        END AS amount
    FROM subscriptions s
    LEFT JOIN latest_payment lp ON lp.subscription_id = s.id
    WHERE s.legacy_renewal_amount IS NULL
      AND LOWER(s.provider) IN ('asaas', 'cakto')
      AND LOWER(s.plan) IN ('professional', 'essencial', 'agency', 'growth', 'scale', 'infinity')
      AND s.created_at < TIMESTAMPTZ '2026-10-15 00:00:00-03'
      AND NOT EXISTS (
          SELECT 1
          FROM checkout_sessions later
          WHERE later.user_id = s.user_id
            AND later.paid_at >= TIMESTAMPTZ '2026-10-15 00:00:00-03'
      )
)
UPDATE subscriptions AS target
SET legacy_renewal_amount = candidates.amount
FROM candidates
WHERE target.id = candidates.subscription_id
  AND target.legacy_renewal_amount IS NULL
  AND candidates.amount >= 10.00;

COMMIT;

-- Conferência: assinaturas dos planos antigos (asaas e cakto, criadas antes do corte) por provider e
-- plano, quantas ficaram com valor de renovação e quantas ficaram sem valor.
SELECT
    LOWER(s.provider) AS provider,
    LOWER(s.plan) AS plano,
    COUNT(*) AS assinaturas,
    COUNT(s.legacy_renewal_amount) AS com_valor,
    COUNT(*) - COUNT(s.legacy_renewal_amount) AS sem_valor,
    MIN(s.legacy_renewal_amount) AS menor_valor,
    MAX(s.legacy_renewal_amount) AS maior_valor
FROM subscriptions s
WHERE LOWER(s.provider) IN ('asaas', 'cakto')
  AND LOWER(s.plan) IN ('professional', 'essencial', 'agency', 'growth', 'scale', 'infinity')
  AND s.created_at < TIMESTAMPTZ '2026-10-15 00:00:00-03'
GROUP BY LOWER(s.provider), LOWER(s.plan)
ORDER BY 1, 2;
