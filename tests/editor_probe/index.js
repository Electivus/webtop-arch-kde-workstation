const assert = require('node:assert/strict');
const fs = require('node:fs');
const vscode = require('vscode');

const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
async function eventually(description, operation) {
    const deadline = Date.now() + 180000;
    while (Date.now() < deadline) {
        const result = await operation();
        if (result) return result;
        await delay(500);
    }
    throw new Error('Timed out: ' + description);
}

exports.run = async () => {
    const result = { editor: vscode.env.appName, version: vscode.version, result: 'running' };
    const checkpoint = step => {
        result.step = step;
        fs.writeFileSync(process.env.ELECTIVUS_TEST_RESULT, JSON.stringify(result, null, 2));
    };
    try {
        checkpoint('open-apex');
        const root = vscode.workspace.workspaceFolders[0].uri;
        const uri = vscode.Uri.joinPath(root, 'force-app/main/default/classes/WorkstationProbe.cls');
        const document = await vscode.workspace.openTextDocument(uri);
        await vscode.window.showTextDocument(document);
        const apex = vscode.extensions.getExtension('salesforce.salesforcedx-vscode-apex');
        const lwc = vscode.extensions.getExtension('salesforce.salesforcedx-vscode-lwc');
        assert(apex && lwc, 'prepared Salesforce extensions must be available to the editor');
        checkpoint('activate-apex');
        await apex.activate();
        checkpoint('apex-diagnostic');
        const diagnostic = await eventually('Apex syntax error', () =>
            vscode.languages.getDiagnostics(uri).find(entry => entry.severity === vscode.DiagnosticSeverity.Error));
        result.apexDiagnostic = diagnostic.message;
        result.apexExtension = apex.packageJSON.version;

        const edit = new vscode.WorkspaceEdit();
        const repaired = 'public class WorkstationProbe { public static Integer value() { return 1; } public static void log() { System.assert(true); } }\n';
        edit.replace(uri, new vscode.Range(document.positionAt(0), document.positionAt(document.getText().length)), repaired);
        await vscode.workspace.applyEdit(edit);
        await document.save();
        checkpoint('apex-repair');
        await eventually('Apex diagnostic cleared after repair', () =>
            vscode.languages.getDiagnostics(uri).filter(entry => entry.severity === vscode.DiagnosticSeverity.Error).length === 0);
        result.apexRepair = 'syntax error cleared after adding the missing semicolon';
        checkpoint('apex-completion');
        await eventually('System.debug method completion', async () => {
            const list = await vscode.commands.executeCommand('vscode.executeCompletionItemProvider', uri,
                document.positionAt(repaired.indexOf('System.') + 'System.'.length), '.');
            return list && list.items.find(item =>
                /^debug/.test(typeof item.label === 'string' ? item.label : item.label.label)
                && [vscode.CompletionItemKind.Method, vscode.CompletionItemKind.Function].includes(item.kind));
        });
        result.apexCompletion = 'System.debug method';

        const html = await vscode.workspace.openTextDocument(
            vscode.Uri.joinPath(root, 'force-app/main/default/lwc/workstationProbe/workstationProbe.html'));
        await vscode.window.showTextDocument(html);
        checkpoint('activate-lwc');
        await lwc.activate();
        checkpoint('lwc-completion');
        const completion = await eventually('Lightning component completion', async () => {
            const list = await vscode.commands.executeCommand('vscode.executeCompletionItemProvider',
                html.uri, new vscode.Position(1, '    <lightning-button '.length));
            return list && list.items.find(item => (typeof item.label === 'string' ? item.label : item.label.label) === 'label');
        });
        assert(completion);
        result.lwcCompletion = 'lightning-button label attribute';
        result.lwcExtension = lwc.packageJSON.version;
        result.result = 'passed';
    } catch (error) {
        result.result = 'failed';
        result.error = String(error.stack || error);
        result.diagnostics = vscode.languages.getDiagnostics().map(([uri, entries]) =>
            ({ file: uri.path, messages: entries.map(entry => entry.message) }));
        throw error;
    } finally {
        fs.writeFileSync(process.env.ELECTIVUS_TEST_RESULT, JSON.stringify(result, null, 2));
        console.log(JSON.stringify(result));
    }
};
