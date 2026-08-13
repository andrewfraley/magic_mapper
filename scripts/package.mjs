import { cpSync, mkdirSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const stage = join(root, "build", "app");
const output = join(root, "dist");
const files = [
  "LICENSE",
  "appinfo.json",
  "assets",
  "css",
  "icon.png",
  "index.html",
  "js",
  "largeIcon.png",
  "magic_mapper.py",
  "magic_mapper_runtime.py",
  "mapperctl.py",
];

if (!stage.startsWith(join(root, "build"))) {
  throw new Error("Refusing to clean a packaging directory outside build/");
}
rmSync(stage, { recursive: true, force: true });
mkdirSync(stage, { recursive: true });
mkdirSync(output, { recursive: true });
for (const file of files) {
  cpSync(join(root, file), join(stage, file), { recursive: true });
}

const packager = join(root, "node_modules", ".bin", "ares-package");
const result = spawnSync(packager, [stage, "--outdir", output], { stdio: "inherit" });
process.exit(result.status ?? 1);
