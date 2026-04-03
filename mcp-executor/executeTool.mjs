import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

async function main() {
  const toolName = process.argv[2];
  const argsStr = process.argv[3] || '{}';
  const args = JSON.parse(argsStr);

  const transport = new StdioClientTransport({
    command: 'notebooklm-mcp',
    args: []
  });

  const client = new Client(
    { name: 'antigravity-mcp-executor', version: '1.0.0' },
    { capabilities: {} }
  );

  try {
    await client.connect(transport);
    
    if (toolName === 'listTools') {
      const result = await client.listTools();
      console.log(JSON.stringify(result, null, 2));
    } else {
      const result = await client.callTool({
        name: toolName,
        arguments: args
      }, { timeout: 300000 });
      console.log(JSON.stringify(result, null, 2));
      if (toolName === 'setup_auth') {
        console.log("Waiting 10 minutes for auth...");
        await new Promise(r => setTimeout(r, 600000));
      }
    }
  } catch (error) {
    console.error("Error:", error);
  } finally {
    process.exit(0);
  }
}

main();
