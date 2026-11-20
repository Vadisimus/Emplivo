const FILE_LIMIT = 5 * 1024 ** 2;
const BODY_LIMIT = FILE_LIMIT + 128 * 1024;
const ORIGIN_ALLOW_HEADERS = 'Content-Type';
const PDF = 'application/pdf';
const DOCX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';

class InputError extends Error {
  constructor(code, status = 400) {
    super(code);
    this.status = status;
  }
}

const csv = (value = '') => value.split(',').map(item => item.trim()).filter(Boolean);

async function readForm(request) {
  const type = request.headers.get('Content-Type') ?? '';
  if (!/^multipart\/form-data\s*;/i.test(type)) throw new InputError('bad_content_type', 415);
  if (Number(request.headers.get('Content-Length')) > BODY_LIMIT) throw new InputError('too_large', 413);
  const reader = request.body?.getReader();
  if (!reader) throw new InputError('missing_body');
  const chunks = [];
  let size = 0;
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > BODY_LIMIT) {
        await reader.cancel();
        throw new InputError('too_large', 413);
      }
      chunks.push(value);
    }
    return await new Response(new Blob(chunks), { headers: { 'Content-Type': type } }).formData();
  } catch (error) {
    if (error instanceof InputError) throw error;
    throw new InputError('bad_multipart');
  } finally {
    reader.releaseLock();
  }
}

function field(form, name, max, optional = false) {
  const values = form.getAll(name);
  if (optional && !values.length) return '';
  const value = values[0];
  if (values.length !== 1 || typeof value !== 'string' || value.length > max) throw new InputError('invalid_fields');
  const text = value.trim();
  if (!optional && !text) throw new InputError('invalid_fields');
  return text;
}

// Inspect the ZIP directory without inflating content. Limit work for malformed archives.
export function isDocx(bytes) {
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  if (view.byteLength < 22 || view.getUint32(0, true) !== 0x04034b50) return false;
  let end = bytes.length - 22;
  const floor = Math.max(0, end - 65535);
  while (end >= floor) {
    if (view.getUint32(end, true) === 0x06054b50 &&
        end + 22 + view.getUint16(end + 20, true) === bytes.length) break;
    end--;
  }
  if (end < floor || view.getUint16(end + 4, true) || view.getUint16(end + 6, true)) return false;
  const entries = view.getUint16(end + 10, true);
  if (!entries || entries > 2048 || view.getUint16(end + 8, true) !== entries) return false;
  const length = view.getUint32(end + 12, true);
  let offset = view.getUint32(end + 16, true);
  if (offset + length !== end) return false;
  let contentTypes = false;
  let document = false;
  const decode = new TextDecoder();
  for (let i = 0; i < entries; i++) {
    if (offset + 46 > end || view.getUint32(offset, true) !== 0x02014b50) return false;
    if (view.getUint16(offset + 8, true) & 1) return false;
    const nameLength = view.getUint16(offset + 28, true);
    const next = offset + 46 + nameLength + view.getUint16(offset + 30, true) +
      view.getUint16(offset + 32, true);
    if (next > end) return false;
    const name = decode.decode(bytes.subarray(offset + 46, offset + 46 + nameLength));
    if (name === '[Content_Types].xml') contentTypes = true;
    if (name === 'word/document.xml') document = true;
    if (/vbaProject\.bin$/i.test(name)) return false;
    offset = next;
  }
  return offset === end && contentTypes && document;
}

async function cvFile(form) {
  const files = form.getAll('cv');
  const file = files[0];
  if (files.length !== 1 || !(file instanceof File) || !file.size) throw new InputError('cv_required');
  if (file.size > FILE_LIMIT) throw new InputError('too_large', 413);
  const suffix = file.name.toLowerCase().split('.').at(-1);
  if (!['pdf', 'docx'].includes(suffix)) throw new InputError('invalid_file', 415);
  if (suffix === 'pdf') {
    if (await file.slice(0, 5).text() !== '%PDF-') throw new InputError('invalid_file', 415);
    return { blob: file.slice(0, file.size, PDF), suffix };
  }
  if (!isDocx(new Uint8Array(await file.arrayBuffer()))) throw new InputError('invalid_file', 415);
  return { blob: file.slice(0, file.size, DOCX), suffix };
}

async function challengeOK(token, origin, kind, env) {
  const response = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
    method: 'POST',
    body: new URLSearchParams({ secret: env.TURNSTILE_SECRET_KEY, response: token }),
    signal: AbortSignal.timeout(6000),
  });
  if (!response.ok) throw new Error('challenge_unavailable');
  const check = await response.json();
  return check.success === true && check.action === kind && check.hostname === new URL(origin).hostname;
}

async function sendToTelegram(env, data) {
  const { id, kind, name, email, phone, company, role, description, vacancy, file, privacy } = data;
  const lines = [kind === 'apply' ? 'Анкета кандидата' : 'Бриф роботодавця', 'ID ' + id, name, email];
  if (kind === 'apply') {
    if (phone) lines.push('Телефон ' + phone);
    lines.push(vacancy ? 'Вакансія ' + vacancy : 'Загальна анкета');
  } else {
    lines.push('Компанія ' + company, 'Посада ' + role, description);
  }
  lines.push('Приватність ' + privacy);
  const body = new FormData();
  body.set('chat_id', env.TELEGRAM_PRIVATE_CHAT_ID);
  if (file) {
    body.set('caption', lines.join('\n'));
    body.set('document', file.blob, id + '.' + file.suffix);
  } else {
    body.set('text', lines.join('\n'));
  }
  try {
    const method = file ? 'sendDocument' : 'sendMessage';
    const response = await fetch('https://api.telegram.org/bot' + env.TELEGRAM_BOT_TOKEN + '/' + method, {
      method: 'POST', body, signal: AbortSignal.timeout(20000),
    });
    const output = await response.json();
    if (response.ok && output.ok === true && Number.isInteger(output.result?.message_id)) return 'sent';
    if (response.status < 500 && output.ok === false) return 'failed';
  } catch {
    // The upstream may have accepted the message before the response was lost.
  }
  return 'unknown';
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') ?? '';
    const headers = new Headers({ 'Cache-Control': 'no-store', 'Vary': 'Origin', 'X-Content-Type-Options': 'nosniff' });
    const reply = (status, body) => Response.json(body, { status, headers });
    const kind = { '/api/apply': 'apply', '/api/employer': 'employer' }[new URL(request.url).pathname];
    if (!kind) return reply(404, { error: 'not_found' });
    if (!csv(env.ALLOWED_ORIGINS).includes(origin)) return reply(403, { error: 'origin' });
    headers.set('Access-Control-Allow-Origin', origin);
    headers.set('Access-Control-Allow-Methods', 'POST, OPTIONS');
    headers.set('Access-Control-Allow-Headers', ORIGIN_ALLOW_HEADERS);
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers });
    if (request.method !== 'POST') {
      headers.set('Allow', 'POST, OPTIONS');
      return reply(405, { error: 'method' });
    }

    // Rate-limit before reading the multipart body. No addresses are written to D1.
    let reserved = false;
    try {
      if (!env.TELEGRAM_BOT_TOKEN || !env.TELEGRAM_PRIVATE_CHAT_ID || !env.TURNSTILE_SECRET_KEY) {
        return reply(503, { error: 'unavailable' });
      }
      const ip = request.headers.get('CF-Connecting-IP');
      if (!ip) return reply(503, { error: 'unavailable' });
      if (!(await env.INTAKE_LIMIT.limit({ key: kind + ':' + ip })).success) return reply(429, { error: 'rate_limit' });

      const form = await readForm(request);
      const id = field(form, 'submissionId', 36);
      if (!/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(id)) {
        throw new InputError('invalid_fields');
      }
      if (field(form, 'consent', 3) !== 'yes') throw new InputError('consent');
      const privacy = field(form, 'privacyVersion', 32);
      if (privacy !== env.PRIVACY_VERSION) throw new InputError('privacy_changed', 409);
      const email = field(form, 'email', 200);
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) throw new InputError('invalid_fields');

      const data = { kind, id, email, privacy, name: field(form, 'name', 120) };
      if (kind === 'apply') {
        data.phone = field(form, 'phone', 40, true);
        data.vacancy = field(form, 'vacancyId', 80, true);
        if (data.vacancy && !csv(env.EMPLIVO_VACANCY_IDS).includes(data.vacancy)) throw new InputError('vacancy_closed', 409);
        data.file = await cvFile(form);
      } else {
        data.company = field(form, 'company', 140);
        data.role = field(form, 'role', 140);
        data.description = field(form, 'description', 2000);
      }
      const token = field(form, 'cf-turnstile-response', 2048);
      if (!(await challengeOK(token, origin, kind, env))) return reply(403, { error: 'challenge' });

      const slot = await env.DB.prepare(
        "INSERT INTO submissions (id, kind, status) VALUES (?, ?, 'pending') " +
        "ON CONFLICT(id) DO UPDATE SET status = 'pending', updated_at = unixepoch() " +
        "WHERE submissions.status = 'failed' AND submissions.kind = excluded.kind",
      ).bind(id, kind).run();
      if (!slot.meta.changes) {
        const previous = await env.DB.prepare('SELECT status, kind FROM submissions WHERE id = ?').bind(id).first();
        return previous?.kind === kind && previous.status === 'sent'
          ? reply(200, { ok: true, id })
          : reply(409, { error: 'delivery_unknown', id });
      }
      reserved = true;
      const status = await sendToTelegram(env, data);
      await env.DB.prepare('UPDATE submissions SET status = ?, updated_at = unixepoch() WHERE id = ?')
        .bind(status, id).run();
      if (status === 'sent') return reply(200, { ok: true, id });
      if (status === 'failed') return reply(502, { error: 'delivery_rejected', id });
      return reply(409, { error: 'delivery_unknown', id });
    } catch (error) {
      if (error instanceof InputError) return reply(error.status, { error: error.message });
      return reserved ? reply(409, { error: 'delivery_unknown' }) : reply(503, { error: 'unavailable' });
    }
  },

  async scheduled(event, env) {
    await env.DB.prepare('DELETE FROM submissions WHERE updated_at < unixepoch() - 7 * 86400').run();
  },
};
