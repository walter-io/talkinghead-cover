#!/usr/bin/env node
/*
 * Agnes 图生图 / 文生图 通用调用脚本
 *
 * 用法:
 *   node agnes_img2img.cjs config.json
 *
 * config.json 字段:
 *   {
 *     "image":  "C:/path/to/character.png",   // 可选；给了就是图生图，不给就是文生图
 *     "prompt": "……",                          // 必填
 *     "out":    "C:/path/to/base.png",         // 必填，输出图片路径
 *     "model":  "agnes-image-2.1-flash",       // 可选，默认 agnes-image-2.1-flash
 *     "size":   "2K",                          // 可选，默认 2K
 *     "ratio":  "9:16"                         // 可选，默认 9:16
 *   }
 *
 * key 读取顺序: 环境变量 AGNES_API_KEY ->  C:\Users\<user>\.agnes_key
 */
const fs = require('fs');
const path = require('path');

const API_BASE = 'https://api.agnes-ai.cn';

function readKey() {
  if (process.env.AGNES_API_KEY && process.env.AGNES_API_KEY.trim()) return process.env.AGNES_API_KEY.trim();
  const f = path.join(process.env.USERPROFILE || process.env.HOME || 'C:\\Users\\we', '.agnes_key');
  if (fs.existsSync(f)) return fs.readFileSync(f, 'utf8').trim();
  throw new Error('缺少 Agnes key：请设置环境变量 AGNES_API_KEY，或写入 ' + f);
}

function mimeOf(p) {
  const e = path.extname(p).toLowerCase();
  if (e === '.jpg' || e === '.jpeg') return 'image/jpeg';
  if (e === '.webp') return 'image/webp';
  return 'image/png';
}

async function main() {
  const cfgPath = process.argv[2];
  if (!cfgPath) throw new Error('用法: node agnes_img2img.cjs config.json');
  const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8').replace(/^\uFEFF/, ''));
  if (!cfg.prompt) throw new Error('config.prompt 必填');
  if (!cfg.out) throw new Error('config.out 必填');

  const API_KEY = readKey();
  const extra = { response_format: 'url' };
  if (cfg.image) {
    const abs = path.resolve(cfg.image);
    const b64 = fs.readFileSync(abs).toString('base64');
    extra.image = [`data:${mimeOf(abs)};base64,${b64}`];
  }

  const res = await fetch(API_BASE + '/v1/images/generations', {
    method: 'POST',
    headers: { 'Authorization': 'Bearer ' + API_KEY, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: cfg.model || 'agnes-image-2.1-flash',
      prompt: cfg.prompt,
      size: cfg.size || '2K',
      ratio: cfg.ratio || '9:16',
      extra_body: extra
    })
  });
  const data = await res.json();
  console.log('status:', res.status);
  const url = data && data.data && data.data[0] && data.data[0].url;
  if (!url) { console.error('no url'); console.error(JSON.stringify(data).slice(0, 800)); process.exit(1); }

  const imgRes = await fetch(url);
  const buf = Buffer.from(await imgRes.arrayBuffer());
  fs.mkdirSync(path.dirname(path.resolve(cfg.out)), { recursive: true });
  fs.writeFileSync(cfg.out, buf);
  console.log('saved:', cfg.out);
}
main().catch(e => { console.error(e); process.exit(1); });
