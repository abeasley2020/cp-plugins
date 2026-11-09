import { execFileSync } from "node:child_process";
import { readdirSync, statSync, readFileSync } from "node:fs";
import { join, relative, sep, dirname } from "node:path";
import { fileURLToPath } from "node:url";

export const REPO_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..");

const SKIP_DIRS = new Set([".git", "node_modules", "_audit", ".vscode", ".idea"]);

const BINARY_EXTENSIONS = new Set([
  ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svgz",
  ".pdf", ".docx", ".pptx", ".xlsx", ".zip", ".gz", ".tar",
  ".mp4", ".mp3", ".wav", ".vtt",
  ".woff", ".woff2", ".ttf", ".otf", ".eot",
]);

function toPosix(path) {
  return path.split(sep).join("/");
}

/**
 * List files tracked or untracked-but-not-ignored by git. Falls back to a
 * directory walk when git is unavailable (for example in a bare copy).
 * Returns repo-relative POSIX paths.
 */
export function listRepoFiles(root = REPO_ROOT) {
  try {
    const out = execFileSync("git", ["ls-files", "--cached", "--others", "--exclude-standard", "-z"], {
      cwd: root,
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
    });
    const files = out.split("\0").filter(Boolean);
    return files.filter((f) => {
      try {
        return statSync(join(root, f)).isFile();
      } catch {
        return false;
      }
    });
  } catch {
    return walk(root, root);
  }
}

function walk(dir, root) {
  const results = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.isDirectory()) {
      if (SKIP_DIRS.has(entry.name)) continue;
      results.push(...walk(join(dir, entry.name), root));
    } else if (entry.isFile()) {
      results.push(toPosix(relative(root, join(dir, entry.name))));
    }
  }
  return results;
}

export function isBinaryPath(path) {
  const dot = path.lastIndexOf(".");
  if (dot === -1) return false;
  return BINARY_EXTENSIONS.has(path.slice(dot).toLowerCase());
}

/** Read a file as UTF-8, or return null when it contains NUL bytes. */
export function readTextFile(absolutePath) {
  const buffer = readFileSync(absolutePath);
  if (buffer.includes(0)) return null;
  return buffer.toString("utf8");
}
