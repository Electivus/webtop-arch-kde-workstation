const assert = require('node:assert/strict');
const fs = require('node:fs');
const https = require('node:https');
const vscode = require('vscode');

function request(url) {
    return new Promise((resolve, reject) => {
        const req = https.get(url, response => {
            const chunks = [];
            response.on('data', chunk => chunks.push(chunk));
            response.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
            response.on('error', reject);
        });
        req.setTimeout(20000, () => req.destroy(new Error('network timeout')));
        req.on('error', reject);
    });
}

exports.run = async () => {
    const result = { editor: vscode.env.appName, version: vscode.version, runtime: process.versions };
    try {
        assert.equal(await request('https://network-target:4443'), 'workstation-network-ok');
        result.validTLS = 'accepted';
        await assert.rejects(request('https://network-target:4444'), error => {
            result.invalidTLS = error.code;
            return /CERT|VERIFY|SELF_SIGNED/.test(error.code || '');
        });
        result.result = 'passed';
    } catch (error) {
        result.result = 'failed';
        result.error = String(error.stack || error);
        throw error;
    } finally {
        fs.writeFileSync(process.env.ELECTIVUS_TEST_RESULT, JSON.stringify(result, null, 2));
    }
};
