import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";

import {
  createHash,
} from "node:crypto";

import {
  lstatSync,
  readFileSync,
  readdirSync,
  realpathSync,
  statSync,
} from "node:fs";

import {
  basename,
  isAbsolute,
  join,
  relative,
  resolve,
  sep,
} from "node:path";

const REPO_ROOT = realpathSync(process.cwd());

const ARTIFACT_REL =
  "reports/validation/artifacts/" +
  "project_memory_v0.1_design_r5_2026-07-29";

const MAIN_REPORT_REL =
  "reports/validation/project_memory_v0.1_design_r5_2026-07-29.md";

const MANIFEST_REL =
  "reports/validation/artifacts/" +
  "project_memory_v0.1_design_r5_2026-07-29/design_manifest.json";

const FOCUSED_PROMPT_REL =
  "reports/validation/artifacts/" +
  "project_memory_v0.1_design_r5_2026-07-29/focused_review_prompt.md";

const MANIFEST_BASENAME = "design_manifest.json";
const MAX_TEXT_BYTES = 2_000_000;

const ARTIFACT_ROOT = realpathSync(resolve(REPO_ROOT, ARTIFACT_REL));
const MAIN_REPORT_PATH = realpathSync(resolve(REPO_ROOT, MAIN_REPORT_REL));
const MANIFEST_PATH = realpathSync(resolve(REPO_ROOT, MANIFEST_REL));

function sha256(data: Buffer | string): string {
  return createHash("sha256").update(data).digest("hex");
}

function readManifest(): {
  sealed_files: Array<{
    path: string;
    size_bytes: number;
    sha256: string;
  }>;
  sealed_payload_count: number;
  sealed_artifact_count: number;
  main_report_count: number;
  design_package_sha256: string;
  package_hash_algorithm: string;
  base_head: string;
  memory_directory_created: boolean;
  production_code_created: boolean;
  staged: boolean;
  committed: boolean;
  pushed: boolean;
} {
  const raw = readFileSync(MANIFEST_PATH);
  const parsed = JSON.parse(raw.toString("utf8")) as {
    sealed_files?: Array<{
      path: string;
      size_bytes: number;
      sha256: string;
    }>;
    sealed_payload_count?: number;
    sealed_artifact_count?: number;
    main_report_count?: number;
    design_package_sha256?: string;
    package_hash_algorithm?: string;
    base_head?: string;
    memory_directory_created?: boolean;
    production_code_created?: boolean;
    staged?: boolean;
    committed?: boolean;
    pushed?: boolean;
  };

  return {
    sealed_files: parsed.sealed_files ?? [],
    sealed_payload_count: parsed.sealed_payload_count ?? 0,
    sealed_artifact_count: parsed.sealed_artifact_count ?? 0,
    main_report_count: parsed.main_report_count ?? 0,
    design_package_sha256: parsed.design_package_sha256 ?? "",
    package_hash_algorithm: parsed.package_hash_algorithm ?? "",
    base_head: parsed.base_head ?? "",
    memory_directory_created: parsed.memory_directory_created ?? false,
    production_code_created: parsed.production_code_created ?? false,
    staged: parsed.staged ?? false,
    committed: parsed.committed ?? false,
    pushed: parsed.pushed ?? false,
  };
}

function buildWhitelist(): Set<string> {
  const manifest = readManifest();
  const allowed = new Set<string>();

  allowed.add(MANIFEST_REL);

  for (const entry of manifest.sealed_files) {
    allowed.add(entry.path);
  }

  return allowed;
}

function normalizeSlashes(input: string): string {
  return input.split("\\").join("/");
}

function safePath(inputPath: string): string {
  const normalized = normalizeSlashes(inputPath).replace(/^\.\//, "");

  if (isAbsolute(normalized)) {
    throw new Error("Absolute paths are forbidden.");
  }

  if (normalized.split("/").includes("..")) {
    throw new Error("Path traversal is forbidden.");
  }

  const repositoryRelative =
    normalized === ARTIFACT_REL ||
    normalized === MAIN_REPORT_REL ||
    normalized.startsWith(`${ARTIFACT_REL}/`);

  let candidate: string;
  let expectedRel: string;

  if (normalized === "." || normalized === "") {
    candidate = ARTIFACT_ROOT;
    expectedRel = ARTIFACT_REL;
  } else if (repositoryRelative) {
    candidate = resolve(REPO_ROOT, normalized);
    expectedRel = normalized;
  } else {
    candidate = resolve(ARTIFACT_ROOT, normalized);
    expectedRel = normalizeSlashes(
      `${ARTIFACT_REL}/${normalized}`,
    );
  }

  let real: string;

  try {
    real = realpathSync(candidate);
  } catch {
    throw new Error("Path does not exist or cannot be resolved.");
  }

  const actualRel = normalizeSlashes(
    relative(REPO_ROOT, real),
  );

  if (actualRel !== expectedRel) {
    throw new Error(
      "Path identity changed after realpath resolution.",
    );
  }

  if (
    actualRel !== MAIN_REPORT_REL &&
    actualRel !== ARTIFACT_REL &&
    !actualRel.startsWith(`${ARTIFACT_REL}/`)
  ) {
    throw new Error(
      "Path escapes the Project Memory r5 review scope.",
    );
  }

  return real;
}

function regularFiles(root: string): string[] {
  const output: string[] = [];

  function walk(dir: string): void {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const full = join(dir, entry.name);

      if (entry.isSymbolicLink()) {
        continue;
      }

      if (entry.isDirectory()) {
        walk(full);
      } else if (entry.isFile()) {
        output.push(full);
      }
    }
  }

  walk(root);
  return output;
}

function textResult(payload: unknown) {
  return {
    content: [
      {
        type: "text" as const,
        text: JSON.stringify(payload, null, 2),
      },
    ],
    details: {},
  };
}

export default function (pi: ExtensionAPI) {
  pi.registerTool({
    name: "review_list",
    label: "Review List",
    description:
      "List files inside the Project Memory v0.1 design r5 package only.",

    parameters: Type.Object({
      path: Type.Optional(
        Type.String({
          description:
            "Artifact-relative directory path. Use '.' for artifact root.",
        }),
      ),
      max_depth: Type.Optional(
        Type.Integer({
          minimum: 0,
          maximum: 8,
          description: "Maximum recursive depth.",
        }),
      ),
    }),

    async execute(_id, rawParams) {
      const params = rawParams as {
        path?: string;
        max_depth?: number;
      };

      const manifest = readManifest();
      const allowed = buildWhitelist();
      const sealedSet = new Set(
        manifest.sealed_files.map((entry) => entry.path),
      );

      const inputPath = params.path ?? ".";
      const root = safePath(inputPath);
      const maxDepth = params.max_depth ?? 1;

      const entries: Array<{
        path: string;
        type: "file" | "directory";
        size_bytes: number | null;
        sealed: boolean;
        readable: boolean;
      }> = [];

      function walk(dir: string, depth: number): void {
        for (const entry of readdirSync(dir, { withFileTypes: true })) {
          const full = join(dir, entry.name);

          if (entry.isSymbolicLink()) {
            continue;
          }

          const rel = normalizeSlashes(relative(REPO_ROOT, full));
          const sealed = sealedSet.has(rel);
          const readable = allowed.has(rel);

          if (entry.isDirectory()) {
            entries.push({
              path: rel,
              type: "directory",
              size_bytes: null,
              sealed: false,
              readable: false,
            });

            if (depth < maxDepth) {
              walk(full, depth + 1);
            }
          } else if (entry.isFile()) {
            entries.push({
              path: rel,
              type: "file",
              size_bytes: statSync(full).size,
              sealed,
              readable,
            });
          }
        }
      }

      walk(root, 0);

      const mainStat = (() => {
        try {
          return lstatSync(MAIN_REPORT_PATH);
        } catch {
          return null;
        }
      })();

      if (mainStat && mainStat.isFile()) {
        entries.push({
          path: MAIN_REPORT_REL,
          type: "file",
          size_bytes: mainStat.size,
          sealed: sealedSet.has(MAIN_REPORT_REL),
          readable: allowed.has(MAIN_REPORT_REL),
        });
      }

      entries.sort((a, b) => a.path.localeCompare(b.path));

      return textResult({
        manifest: MANIFEST_REL,
        main_report: MAIN_REPORT_REL,
        entries,
      });
    },
  });

  pi.registerTool({
    name: "review_read",
    label: "Review Read",
    description:
      "Read a UTF-8 text file inside the Project Memory v0.1 design r5 package only.",

    parameters: Type.Object({
      path: Type.String({
        description: "Repository-relative file path.",
      }),
      start_line: Type.Optional(
        Type.Integer({
          minimum: 1,
          description: "First line, one-based.",
        }),
      ),
      end_line: Type.Optional(
        Type.Integer({
          minimum: 1,
          description: "Last line, inclusive.",
        }),
      ),
    }),

    async execute(_id, rawParams) {
      const params = rawParams as {
        path: string;
        start_line?: number;
        end_line?: number;
      };

      const allowed = buildWhitelist();
      const rel = params.path;

      if (!allowed.has(rel)) {
        throw new Error("Requested path is outside the sealed whitelist.");
      }

      const full = safePath(rel);
      const info = lstatSync(full);

      if (!info.isFile()) {
        throw new Error("Requested path is not a regular file.");
      }

      if (info.size > MAX_TEXT_BYTES) {
        throw new Error("File exceeds the guarded text-size limit.");
      }

      const data = readFileSync(full);

      if (data.includes(0)) {
        throw new Error("Binary files cannot be read with review_read.");
      }

      const lines = data.toString("utf8").split(/\r?\n/);
      const start = params.start_line ?? 1;
      const end = Math.min(
        params.end_line ?? lines.length,
        lines.length,
      );

      if (end < start) {
        throw new Error(
          "end_line must be greater than or equal to start_line.",
        );
      }

      const selected = lines
        .slice(start - 1, end)
        .map((line, index) => `${start + index}: ${line}`)
        .join("\n");

      return {
        content: [
          {
            type: "text" as const,
            text: selected,
          },
        ],
        details: {},
      };
    },
  });

  pi.registerTool({
    name: "review_search",
    label: "Review Search",
    description:
      "Search for fixed text inside UTF-8 files in the Project Memory v0.1 design r5 package.",

    parameters: Type.Object({
      query: Type.String({
        minLength: 1,
        description: "Fixed text to search for.",
      }),
      path: Type.Optional(
        Type.String({
          description: "Repository-relative file or directory.",
        }),
      ),
      case_sensitive: Type.Optional(
        Type.Boolean({
          description: "Whether matching is case-sensitive.",
        }),
      ),
      max_results: Type.Optional(
        Type.Integer({
          minimum: 1,
          maximum: 300,
        }),
      ),
    }),

    async execute(_id, rawParams) {
      const params = rawParams as {
        query: string;
        path?: string;
        case_sensitive?: boolean;
        max_results?: number;
      };

      const allowed = buildWhitelist();
      const limit = params.max_results ?? 100;
      const needle = params.case_sensitive
        ? params.query
        : params.query.toLowerCase();

      let targetFiles: string[];

      if (params.path === undefined) {
        targetFiles = [...allowed];
      } else {
        const inputPath = normalizeSlashes(params.path);

        if (allowed.has(inputPath)) {
          targetFiles = [inputPath];
        } else {
          const artifactPrefix = ARTIFACT_REL + "/";

          if (inputPath === ARTIFACT_REL || inputPath === artifactPrefix) {
            targetFiles = [...allowed].filter(
              (rel) => rel !== MAIN_REPORT_REL,
            );
          } else if (inputPath.startsWith(artifactPrefix)) {
            targetFiles = [...allowed].filter((rel) =>
              rel.startsWith(inputPath),
            );
          } else {
            throw new Error(
              "Requested search path is outside the sealed whitelist.",
            );
          }

          if (targetFiles.length === 0) {
            throw new Error(
              "Requested search path is outside the sealed whitelist.",
            );
          }
        }
      }

      const matches: Array<{
        path: string;
        line: number;
        text: string;
      }> = [];

      for (const rel of targetFiles) {
        const full = safePath(rel);
        const info = statSync(full);

        if (info.size > MAX_TEXT_BYTES) {
          continue;
        }

        const data = readFileSync(full);

        if (data.includes(0)) {
          continue;
        }

        const lines = data.toString("utf8").split(/\r?\n/);

        for (let index = 0; index < lines.length; index += 1) {
          const haystack = params.case_sensitive
            ? lines[index]
            : lines[index].toLowerCase();

          if (haystack.includes(needle)) {
            matches.push({
              path: rel,
              line: index + 1,
              text: lines[index],
            });

            if (matches.length >= limit) {
              return textResult({
                query: params.query,
                truncated: true,
                matches,
              });
            }
          }
        }
      }

      return textResult({
        query: params.query,
        truncated: false,
        matches,
      });
    },
  });

  pi.registerTool({
    name: "review_file_sha256",
    label: "Review File SHA-256",
    description:
      "Compute exact byte size and SHA-256 for Project Memory r5 package files.",

    parameters: Type.Object({
      paths: Type.Array(
        Type.String({
          description: "Repository-relative file path.",
        }),
        {
          minItems: 1,
          maxItems: 100,
        },
      ),
    }),

    async execute(_id, rawParams) {
      const params = rawParams as {
        paths: string[];
      };

      const allowed = buildWhitelist();

      const results = params.paths.map((rel) => {
        if (!allowed.has(rel)) {
          throw new Error("Requested path is outside the sealed whitelist.");
        }

        const full = safePath(rel);
        const data = readFileSync(full);

        return {
          path: rel,
          size_bytes: data.length,
          sha256: sha256(data),
        };
      });

      return textResult({ files: results });
    },
  });

  pi.registerTool({
    name: "review_json_identity",
    label: "Review JSON Identity",
    description:
      "Inspect raw JSON identity inside the Project Memory r5 package.",

    parameters: Type.Object({
      path: Type.String({
        description: "Repository-relative JSON file path.",
      }),
    }),

    async execute(_id, rawParams) {
      const params = rawParams as {
        path: string;
      };

      const allowed = buildWhitelist();
      const rel = params.path;

      if (!allowed.has(rel)) {
        throw new Error("Requested path is outside the sealed whitelist.");
      }

      const full = safePath(rel);
      const raw = readFileSync(full);
      const hasBom =
        raw.length >= 3 &&
        raw[0] === 0xef &&
        raw[1] === 0xbb &&
        raw[2] === 0xbf;

      const text = hasBom
        ? raw.subarray(3).toString("utf8")
        : raw.toString("utf8");

      JSON.parse(text);

      return textResult({
        path: rel,
        raw_size_bytes: raw.length,
        raw_sha256: sha256(raw),
        has_utf8_bom: hasBom,
        ends_with_lf:
          raw.length > 0 && raw[raw.length - 1] === 0x0a,
        ends_with_crlf:
          raw.length > 1 &&
          raw[raw.length - 2] === 0x0d &&
          raw[raw.length - 1] === 0x0a,
      });
    },
  });

  pi.registerTool({
    name: "review_package_identity",
    label: "Review Package Identity",
    description:
      "Rebuild and compare the Project Memory r5 package identity from exact bytes.",

    parameters: Type.Object({}),

    async execute() {
      const manifest = readManifest();

      const mainReportFull = MAIN_REPORT_PATH;
      const mainReportExists = (() => {
        try {
          return lstatSync(mainReportFull).isFile();
        } catch {
          return false;
        }
      })();

      const artifactRecords = regularFiles(ARTIFACT_ROOT)
        .map((full) => {
          const rel = normalizeSlashes(relative(REPO_ROOT, full));
          const data = readFileSync(full);

          return {
            path: rel,
            size_bytes: data.length,
            sha256: sha256(data),
          };
        })
        .filter(
          (entry) =>
            basename(entry.path) !== ".DS_Store" &&
            basename(entry.path) !== MANIFEST_BASENAME,
        );

      const payload = [...artifactRecords];

      if (mainReportExists) {
        const mainData = readFileSync(mainReportFull);
        payload.push({
          path: MAIN_REPORT_REL,
          size_bytes: mainData.length,
          sha256: sha256(mainData),
        });
      }

      payload.sort((a, b) => a.path.localeCompare(b.path));

      const encodedLines = payload.map(
        (entry) => `${entry.path}\t${entry.size_bytes}\t${entry.sha256}\n`,
      );
      const concatenated = Buffer.from(
        encodedLines.join(""),
        "utf8",
      );
      const recomputedPackageSha = sha256(concatenated);

      const declaredSet = new Set(
        manifest.sealed_files.map((entry) => entry.path),
      );
      const recomputedSet = new Set(payload.map((entry) => entry.path));

      const missing = manifest.sealed_files
        .filter((entry) => !recomputedSet.has(entry.path))
        .map((entry) => entry.path);

      const extra = payload
        .filter((entry) => !declaredSet.has(entry.path))
        .map((entry) => entry.path);

      const declaredByPath = new Map(
        manifest.sealed_files.map((entry) => [entry.path, entry]),
      );

      const recomputedByPath = new Map(
        payload.map((entry) => [entry.path, entry]),
      );

      const mismatches: Array<{
        path: string;
        expected: {
          size_bytes: number;
          sha256: string;
        } | null;
        actual: {
          size_bytes: number;
          sha256: string;
        } | null;
      }> = [];

      for (const path of declaredSet) {
        const expected = declaredByPath.get(path) ?? null;
        const actual = recomputedByPath.get(path) ?? null;

        if (
          expected &&
          actual &&
          (
            expected.size_bytes !== actual.size_bytes ||
            expected.sha256 !== actual.sha256
          )
        ) {
          mismatches.push({
            path,
            expected: {
              size_bytes: expected.size_bytes,
              sha256: expected.sha256,
            },
            actual: {
              size_bytes: actual.size_bytes,
              sha256: actual.sha256,
            },
          });
        }
      }

      let allSizeBytesMatch = true;
      let allFileSha256Match = true;

      if (missing.length > 0 || extra.length > 0) {
        allSizeBytesMatch = false;
        allFileSha256Match = false;
      } else {
        for (const path of declaredSet) {
          const expected = declaredByPath.get(path);
          const actual = recomputedByPath.get(path);

          if (!expected || !actual) {
            allSizeBytesMatch = false;
            allFileSha256Match = false;
            break;
          }

          if (expected.size_bytes !== actual.size_bytes) {
            allSizeBytesMatch = false;
          }

          if (expected.sha256 !== actual.sha256) {
            allFileSha256Match = false;
          }
        }
      }

      const dsStorePresent: string[] = [];
      for (const full of regularFiles(ARTIFACT_ROOT)) {
        if (basename(full) === ".DS_Store") {
          dsStorePresent.push(normalizeSlashes(relative(REPO_ROOT, full)));
        }
      }

      const manifestExcluded =
        !declaredSet.has(MANIFEST_REL) &&
        !recomputedSet.has(MANIFEST_REL);

      const mainReportIncluded =
        declaredSet.has(MAIN_REPORT_REL) &&
        recomputedSet.has(MAIN_REPORT_REL);

      const focusedPromptIncluded =
        declaredSet.has(FOCUSED_PROMPT_REL) &&
        recomputedSet.has(FOCUSED_PROMPT_REL);

      const dsStoreIncluded =
        [...declaredSet, ...recomputedSet].some(
          (path) => basename(path) === ".DS_Store",
        );

      return textResult({
        package_hash_algorithm: manifest.package_hash_algorithm,
        package_sha_expected: manifest.design_package_sha256,
        package_sha_recomputed: recomputedPackageSha,
        package_sha256_match:
          manifest.design_package_sha256 === recomputedPackageSha,
        sealed_member_set_match:
          missing.length === 0 && extra.length === 0,
        declared_payload_count: manifest.sealed_payload_count,
        recomputed_payload_count: payload.length,
        declared_artifact_count: manifest.sealed_artifact_count,
        recomputed_artifact_count: artifactRecords.length,
        declared_main_report_count: manifest.main_report_count,
        recomputed_main_report_count: mainReportExists ? 1 : 0,
        all_size_bytes_match: allSizeBytesMatch,
        all_file_sha256_match: allFileSha256Match,
        manifest_excluded: manifestExcluded,
        main_report_included: mainReportIncluded,
        focused_prompt_included: focusedPromptIncluded,
        ds_store_included: dsStoreIncluded,
        ds_store_present_paths: dsStorePresent,
        missing,
        extra,
        mismatches,
        files: payload,
        manifest_project_state: {
          base_head: manifest.base_head,
          memory_directory_created: manifest.memory_directory_created,
          production_code_created: manifest.production_code_created,
          staged: manifest.staged,
          committed: manifest.committed,
          pushed: manifest.pushed,
        },
      });
    },
  });
}
