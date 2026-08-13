import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { basename, join } from "node:path";
import { dirname } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const app = JSON.parse(readFileSync(join(root, "appinfo.json"), "utf8"));
const repository = process.env.GITHUB_REPOSITORY || "andrewfraley/magic_mapper";
const ipkName = `${app.id}_${app.version}_all.ipk`;
const ipkPath = join(root, "dist", ipkName);
const manifestPath = join(root, "dist", `${app.id}.manifest.json`);
const sha256 = createHash("sha256").update(readFileSync(ipkPath)).digest("hex");

const manifest = {
  id: app.id,
  version: app.version,
  type: app.type,
  title: app.title,
  appDescription: "Discover, disable, and remap LG Magic Remote buttons from the TV",
  iconUri: `https://github.com/${repository}/releases/latest/download/${basename(app.largeIcon)}`,
  sourceUrl: `https://github.com/${repository}`,
  rootRequired: true,
  ipkUrl: ipkName,
  ipkHash: { sha256 },
};

writeFileSync(manifestPath, `${JSON.stringify(manifest)}\n`);
console.log(manifestPath);
