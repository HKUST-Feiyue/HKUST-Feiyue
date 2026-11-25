// Cross-runtime contract fixture; the RSA key is ephemeral and test-only.
import { generateKeyPairSync, webcrypto } from 'node:crypto';
import { validate, issueFor } from '../worker/src/index.js';
const { privateKey } = generateKeyPairSync('rsa', { modulusLength: 2048 });
const pem = privateKey.export({type:'pkcs8',format:'pem'});
const key = await webcrypto.subtle.importKey('pkcs8', privateKey.export({type:'pkcs8',format:'der'}), {name:'RSASSA-PKCS1-v1_5',hash:'SHA-256'}, false, ['sign']);
const record = validate({...JSON.parse(process.argv[2]), turnstileToken:'test-only'});
const issue = await issueFor(record, key);
console.log(JSON.stringify({pem,issue:{...issue,labels:issue.labels.map(name=>({name}))}}));
