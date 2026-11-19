import { z } from "zod";

export const RISK_LEGEND =
  "Orden de prioridad retrospectivo. La posición no representa una probabilidad calibrada ni una autorización para uso operativo.";
const hash = z.string().regex(/^[0-9a-f]{64}$/);
const code = z.string().regex(/^(50|73)[0-9]{3}$/);
const period = z.string().regex(/^20[0-9]{2}-(0[1-9]|1[0-2])$/);
export const prioritySchema = z.strictObject({
  municipality_code: code,
  municipality_name: z.string().min(1).max(150),
  department_code: z.enum(["50", "73"]),
  department_name: z.enum(["Meta", "Tolima"]),
  risk_rank: z.number().int().min(1).max(76).nullable(),
  selected_for_attention: z.boolean(),
  eligibility_status: z.enum(["ELIGIBLE", "INELIGIBLE"]),
  ineligibility_reason: z
    .enum(["ORIGIN_STATE_MISSING", "EXCESS_AT_ORIGIN", "REQUIRED_PREDICTORS_MISSING"])
    .nullable(),
});
const traceSchema = z.strictObject({
  recipe_sha256: z.literal("7d67f0595cfdd990e331682ae581d4f49d1f74f83a107f4d9474540412443ec8"),
  recipe_commit: z.literal("a9c2c1abac386053b2e78f072bdb44e0141f4045"),
  model_family: z.literal("logistic_onset"),
  adapter_version: z.literal("v1"),
  library_version: z.literal("1.7.2"),
  artifact_sha256: hash,
  effective_state_sha256: hash,
  training_keys_sha256: hash,
  preparation_sha256: hash,
  predictors_sha256: hash,
  raw_manifest_sha256: hash,
  code_sha: z.string().regex(/^[0-9a-f]{40}$/),
  code_tree_sha256: hash,
  lock_sha256: hash,
  feature_sha256: hash,
  procedure_id: z.literal("SATD-RISK-2025-LOG-CLIMATE-v1"),
  procedure_sha256: hash,
  training_target_start: z.literal("2012-01"),
  training_target_end: z.literal("2024-09"),
  training_available_end: z.literal("2024-10"),
  first_origin: z.literal("2024-11"),
  artifact_contract: z.literal("satd-frozen-logistic-v1"),
});
export const riskRankingSchema = z
  .strictObject({
    schema_version: z.literal("satd-risk-ranking-v1"),
    reference_period: period,
    horizon: z.literal("T2"),
    target_period: z.string().regex(/^2025-(0[1-9]|1[0-2])$/),
    data_cutoff: period,
    logical_generated_at: z.literal("2024-11-01T00:00:00Z"),
    data_version: z.string().min(1).max(128),
    data_kind: z.enum(["CONSOLIDATED_RETROSPECTIVE", "SYNTHETIC"]),
    selection_budget: z.literal(8),
    selection_scope: z.literal("META_TOLIMA_GLOBAL"),
    population_count: z.literal(76),
    eligible_count: z.number().int().min(8).max(76),
    tie_break: z.literal("SCORE_DESC_DIVIPOLA_ASC"),
    trace: traceSchema,
    governance: z.strictObject({
      report_selection: z.literal("SELECTED"),
      historical_reproduction: z.literal("APPROVED"),
      operational_use: z.literal("NOT_AUTHORIZED"),
      champion_status: z.literal("NOT_SELECTED"),
      limitation: z.literal(RISK_LEGEND),
    }),
    municipalities: z.array(prioritySchema).length(76),
  })
  .superRefine((d, ctx) => {
    const error = (message: string) => ctx.addIssue({ code: "custom", message });
    const [year, month] = d.target_period.split("-").map(Number);
    const index = year * 12 + month - 3;
    const origin = `${Math.floor(index / 12)}-${String((index % 12) + 1).padStart(2, "0")}`;
    if (d.reference_period !== origin || d.data_cutoff !== origin) error("Calendario incompatible");
    const codes = d.municipalities.map((t) => t.municipality_code);
    if (codes.join() !== [...new Set(codes)].sort().join()) error("Claves incompatibles");
    if (
      d.municipalities.filter((t) => t.department_code === "50").length !== 29 ||
      d.municipalities.filter((t) => t.department_code === "73").length !== 47
    ) {
      error("Universo territorial incompleto");
    }
    const ranks: number[] = [];
    for (const t of d.municipalities) {
      if (
        !t.municipality_code.startsWith(t.department_code) ||
        t.department_name !== (t.department_code === "50" ? "Meta" : "Tolima")
      ) {
        error("Identidad territorial incompatible");
      }
      const eligible = t.eligibility_status === "ELIGIBLE";
      if (eligible !== (t.risk_rank !== null) || eligible !== (t.ineligibility_reason === null)) {
        error("Elegibilidad incoherente");
      }
      if (t.selected_for_attention !== (t.risk_rank !== null && t.risk_rank <= 8)) {
        error("Selección incompatible");
      }
      if (t.risk_rank !== null) ranks.push(t.risk_rank);
    }
    if (
      ranks.sort((a, b) => a - b).join() !==
      Array.from({ length: d.eligible_count }, (_, i) => i + 1).join()
    ) {
      error("Ranking incompleto o duplicado");
    }
  });
export const riskViewSchema = z
  .strictObject({
    ranking: riskRankingSchema,
    department_filter: z.enum(["50", "73"]).nullable(),
    visible_municipality_codes: z.array(code).max(76),
  })
  .superRefine((v, ctx) => {
    const expected = v.ranking.municipalities
      .filter((t) => v.department_filter === null || t.department_code === v.department_filter)
      .map((t) => t.municipality_code);
    if (expected.join() !== v.visible_municipality_codes.join()) {
      ctx.addIssue({ code: "custom", message: "Filtro incompatible con el documento global" });
    }
  });
export const riskPeriodsSchema = z
  .array(z.string().regex(/^2025-(0[1-9]|1[0-2])$/))
  .refine((p) => p.join() === [...new Set(p)].sort().join(), "Índice incompatible");
export type Priority = z.infer<typeof prioritySchema>;
export type RiskRanking = z.infer<typeof riskRankingSchema>;
