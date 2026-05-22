#!/usr/bin/env node
const { Files } = require('@adobe/aio-sdk')
const fs = require('fs')
const path = require('path')

const INDEX_FILE = path.join(__dirname, '..', 'commerce_brain_index.json')
const FILE_NAME = 'commerce_brain_index.json'
// Set these from app-builder/.env or environment variables
const NAMESPACE = process.env.AIO_RUNTIME_NAMESPACE
const AUTH = process.env.AIO_RUNTIME_AUTH

async function main() {
  if (!NAMESPACE || !AUTH) {
    console.error('ERROR: Set AIO_RUNTIME_NAMESPACE and AIO_RUNTIME_AUTH env vars (from app-builder/.env)')
    process.exit(1)
  }
  const size = Math.round(fs.statSync(INDEX_FILE).size / 1024)
  console.log(`Uploading ${INDEX_FILE} (${size} KB)...`)
  const files = await Files.init({ ow: { namespace: NAMESPACE, auth: AUTH } })
  const content = fs.readFileSync(INDEX_FILE)
  await files.write(FILE_NAME, content)
  console.log(`Done! Uploaded: ${FILE_NAME}`)
}

main().catch(e => { console.error('Failed:', e.message); process.exit(1) })
