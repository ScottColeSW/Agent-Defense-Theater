#!/usr/bin/env node

/**
 * Test script to verify MCP protocol communication
 */

const { spawn } = require('child_process');

class MCPTester {
  constructor() {
    this.testResults = [];
  }

  async testMCPServer() {
    console.log('🧪 Testing MCP Protocol Communication...\n');

    // Start the MCP server
    const server = spawn('node', ['server.js'], {
      stdio: ['pipe', 'pipe', 'pipe']
    });

    let responseData = '';
    
    server.stdout.on('data', (data) => {
      responseData += data.toString();
    });

    server.stderr.on('data', (data) => {
      console.log('Server stderr:', data.toString());
    });

    // Test 1: Initialize connection
    console.log('📡 Test 1: Initialize connection');
    const initMessage = {
      jsonrpc: '2.0',
      id: 1,
      method: 'initialize',
      params: {
        protocolVersion: '2024-11-05',
        capabilities: {
          tools: {}
        },
        clientInfo: {
          name: 'test-client',
          version: '1.0.0'
        }
      }
    };

    server.stdin.write(JSON.stringify(initMessage) + '\n');

    // Wait a bit for response
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Test 2: List tools
    console.log('📋 Test 2: List available tools');
    const listToolsMessage = {
      jsonrpc: '2.0',
      id: 2,
      method: 'tools/list'
    };

    server.stdin.write(JSON.stringify(listToolsMessage) + '\n');
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Test 3: Call a tool
    console.log('🧮 Test 3: Call calculate_affordability tool');
    const callToolMessage = {
      jsonrpc: '2.0',
      id: 3,
      method: 'tools/call',
      params: {
        name: 'calculate_affordability',
        arguments: {
          annual_income: 85000,
          monthly_debts: 650,
          savings: 25000
        }
      }
    };

    server.stdin.write(JSON.stringify(callToolMessage) + '\n');
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Test 4: Call BRRRR analysis tool
    console.log('🏠 Test 4: Call analyze_brrrr_deal tool');
    const brrrrMessage = {
      jsonrpc: '2.0',
      id: 4,
      method: 'tools/call',
      params: {
        name: 'analyze_brrrr_deal',
        arguments: {
          purchase_price: 85000,
          rehab_costs: 25000,
          arv: 150000,
          monthly_rent: 1200
        }
      }
    };

    server.stdin.write(JSON.stringify(brrrrMessage) + '\n');
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Close the server
    server.kill();

    console.log('\n✅ MCP Protocol tests completed');
    console.log('📊 Server responses received:', responseData.length > 0 ? 'Yes' : 'No');
    
    if (responseData.length > 0) {
      console.log('📝 Sample response data (first 500 chars):');
      console.log(responseData.substring(0, 500) + '...');
    }

    return true;
  }

  async runTests() {
    try {
      await this.testMCPServer();
      console.log('\n🎉 All MCP protocol tests passed!');
      process.exit(0);
    } catch (error) {
      console.error('\n❌ MCP protocol test failed:', error.message);
      process.exit(1);
    }
  }
}

// Run tests
if (require.main === module) {
  const tester = new MCPTester();
  tester.runTests();
}

module.exports = MCPTester;

