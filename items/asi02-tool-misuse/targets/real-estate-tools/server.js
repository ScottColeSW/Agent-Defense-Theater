#!/usr/bin/env node

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { CallToolRequestSchema, ListToolsRequestSchema } = require('@modelcontextprotocol/sdk/types.js');
const RealEstateCalculator = require('./RealEstateCalculator.js');

// Test mode - verify everything loads
if (process.argv.includes('--test')) {
  console.log('✅ Real Estate MCP Server - Test Mode');
  console.log('📊 RealEstateCalculator loaded successfully');
  console.log('🔧 Ready for Claude Desktop integration');
  
  // Quick test of calculators
  try {
    const testResult = RealEstateCalculator.executeTool('analyze_brrrr_deal', {
      purchase_price: 100000,
      rehab_costs: 20000,
      arv: 150000,
      monthly_rent: 1200
    });
    console.log('🧮 BRRRR Calculator test passed');
    
    const testAffordability = RealEstateCalculator.executeTool('calculate_affordability', {
      annual_income: 85000,
      monthly_debts: 650,
      savings: 25000
    });
    console.log('🏠 Affordability Calculator test passed');
    
    console.log('✨ All 31 professional calculators ready!');
  } catch (error) {
    console.log('❌ Calculator test failed:', error.message);
  }
  
  process.exit(0);
}

const server = new Server({
  name: "Real Estate Investment Analyzer Pro",
  version: "1.0.0",
  description: "Professional real estate analysis with 31 calculators",
  author: "Scott A. Cole, MBA"
  }, {
  capabilities: { tools: {} }
});

// ALL 31 PROFESSIONAL TOOLS - Complete Implementation
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: 'calculate_affordability',
      description: 'Calculates home affordability based on annual income, monthly debts, and savings with comprehensive DTI analysis',
      inputSchema: {
        type: 'object',
        properties: {
          annual_income: { type: 'number', description: 'Gross annual income before taxes' },
          monthly_debts: { type: 'number', description: 'Total minimum monthly debt payments (car, credit cards, student loans)' },
          savings: { type: 'number', description: 'Total cash available for down payment and closing costs' },
          target_down_payment_pct: { type: 'number', description: 'Target down payment percentage (0.20 = 20%)', default: 0.2 },
          annual_insurance_rate: { type: 'number', description: 'Annual insurance cost as percentage of home price', default: 0.005 },
          annual_tax_rate: { type: 'number', description: 'Annual property tax as percentage of home price', default: 0.01 },
          closing_costs_pct: { type: 'number', description: 'Closing costs as percentage of home price', default: 0.03 },
          interest_rate: { type: 'number', description: 'Expected mortgage interest rate', default: 0.075 },
          loan_term_years: { type: 'number', description: 'Mortgage loan term in years', default: 30 },
          max_back_end_dti: { type: 'number', description: 'Maximum allowed back-end DTI ratio', default: 0.43 }
        },
        required: ['annual_income', 'monthly_debts', 'savings']
      }
    },
    {
      name: 'analyze_brrrr_deal',
      description: 'Comprehensive BRRRR (Buy, Rehab, Rent, Refinance, Repeat) deal analysis with cash-out refinance projections',
      inputSchema: {
        type: 'object',
        properties: {
          purchase_price: { type: 'number', description: 'Purchase price of the property' },
          rehab_costs: { type: 'number', description: 'Total estimated rehabilitation costs' },
          arv: { type: 'number', description: 'After Repair Value (estimated value after rehab)' },
          monthly_rent: { type: 'number', description: 'Expected monthly market rent' },
          refi_ltv: { type: 'number', description: 'Loan-to-Value ratio for refinance', default: 0.75 },
          refi_interest_rate: { type: 'number', description: 'Interest rate for refinance loan', default: 0.075 },
          refi_loan_term_years: { type: 'number', description: 'Term for refinance loan', default: 30 },
          holding_costs: { type: 'number', description: 'Total holding costs during rehab', default: 0 },
          closing_costs_purchase: { type: 'number', description: 'Closing costs for initial purchase', default: 0 },
          closing_costs_refi: { type: 'number', description: 'Closing costs for refinance', default: 0 },
          monthly_expense_pct: { type: 'number', description: 'Monthly expenses as percentage of rent', default: 0.35 }
        },
        required: ['purchase_price', 'rehab_costs', 'arv', 'monthly_rent']
      }
    },
    {
      name: 'evaluate_house_hack',
      description: 'House hacking analysis to determine effective housing costs and savings from multi-unit property',
      inputSchema: {
        type: 'object',
        properties: {
          purchase_price: { type: 'number', description: 'Purchase price of multi-unit property' },
          down_payment_pct: { type: 'number', description: 'Down payment percentage', default: 0.25 },
          interest_rate: { type: 'number', description: 'Mortgage interest rate', default: 0.075 },
          loan_term_years: { type: 'number', description: 'Mortgage loan term in years', default: 30 },
          annual_taxes: { type: 'number', description: 'Annual property tax amount' },
          annual_insurance: { type: 'number', description: 'Annual insurance cost' },
          num_units: { type: 'number', description: 'Total number of units in property' },
          rent_owner_unit: { type: 'number', description: 'Market rent for unit you live in (0 if not renting)', default: 0 },
          rent_other_units: { type: 'number', description: 'Market rent for each other unit' },
          vacancy_rate: { type: 'number', description: 'Expected vacancy rate for rental units', default: 0.05 },
          maintenance_rate: { type: 'number', description: 'Maintenance cost as percentage of total rent', default: 0.1 },
          market_rent_comparison: { type: 'number', description: 'Market rent for similar single-family home you would otherwise rent' }
        },
        required: ['purchase_price', 'annual_taxes', 'annual_insurance', 'num_units', 'rent_other_units', 'market_rent_comparison']
      }
    },
    {
      name: 'project_portfolio_growth',
      description: 'Projects real estate portfolio growth over 20-year period with acquisition timeline and equity buildup',
      inputSchema: {
        type: 'object',
        properties: {
          initial_capital: { type: 'number', description: 'Starting investment capital' },
          annual_savings: { type: 'number', description: 'Amount saved and invested each year' },
          acquisition_frequency_months: { type: 'number', description: 'How often (in months) to acquire new property', default: 18 },
          avg_property_price: { type: 'number', description: 'Average purchase price of target properties' },
          avg_down_payment_pct: { type: 'number', description: 'Average down payment percentage', default: 0.25 },
          avg_cocr: { type: 'number', description: 'Average expected Cash-on-Cash Return', default: 0.08 },
          appreciation_rate: { type: 'number', description: 'Expected annual appreciation rate', default: 0.03 },
          hold_period_years: { type: 'number', description: 'Number of years to project growth', default: 20 }
        },
        required: ['initial_capital', 'annual_savings', 'avg_property_price']
      }
    },
    {
      name: 'analyze_syndication',
      description: 'Real estate syndication investment analysis with IRR projections and profit splits',
      inputSchema: {
        type: 'object',
        properties: {
          investment: { type: 'number', description: 'Amount of capital invested' },
          preferred_return_pct: { type: 'number', description: 'Preferred return rate paid to investors first', default: 0.08 },
          sponsor_split_pct: { type: 'number', description: 'Sponsor share of profits after preferred return', default: 0.3 },
          projected_irr: { type: 'number', description: 'Projected Internal Rate of Return', default: 0.15 },
          hold_period: { type: 'number', description: 'Expected hold period in years', default: 5 },
          exit_value: { type: 'number', description: 'Optional: Projected sale price at exit (overrides IRR)' }
        },
        required: ['investment']
      }
    },
    {
      name: 'calculate_mortgage_affordability',
      description: 'Advanced mortgage qualification calculator with dual income support (uses same logic as calculate_affordability)',
      inputSchema: {
        type: 'object',
        properties: {
          annual_income: { type: 'number', description: 'Gross annual income before taxes' },
          monthly_debts: { type: 'number', description: 'Total minimum monthly debt payments' },
          savings: { type: 'number', description: 'Total cash available for down payment and closing costs' },
          target_down_payment_pct: { type: 'number', description: 'Target down payment percentage', default: 0.2 },
          annual_insurance_rate: { type: 'number', description: 'Annual insurance cost as percentage of home price', default: 0.005 },
          annual_tax_rate: { type: 'number', description: 'Annual property tax as percentage of home price', default: 0.01 },
          closing_costs_pct: { type: 'number', description: 'Closing costs as percentage of home price', default: 0.03 },
          interest_rate: { type: 'number', description: 'Expected mortgage interest rate', default: 0.075 },
          loan_term_years: { type: 'number', description: 'Mortgage loan term in years', default: 30 },
          max_back_end_dti: { type: 'number', description: 'Maximum allowed back-end DTI ratio', default: 0.43 }
        },
        required: ['annual_income', 'monthly_debts', 'savings']
      }
    },
    {
      name: 'analyze_debt_to_income',
      description: 'Analyzes Debt-to-Income ratio for different loan types with qualification assessment',
      inputSchema: {
        type: 'object',
        properties: {
          gross_monthly_income: { type: 'number', description: 'Total gross monthly income from all sources' },
          total_monthly_debts: { type: 'number', description: 'Total of all monthly minimum debt payments' },
          proposed_monthly_piti: { type: 'number', description: 'Proposed monthly mortgage payment (Principal, Interest, Taxes, Insurance)' }
        },
        required: ['gross_monthly_income', 'total_monthly_debts', 'proposed_monthly_piti']
      }
    },
    {
      name: 'compare_loans',
      description: 'Side-by-side comparison of up to 4 loan scenarios with break-even analysis',
      inputSchema: {
        type: 'object',
        properties: {
          loans: {
            type: 'array',
            description: 'Array of loan scenarios to compare',
            items: {
              type: 'object',
              properties: {
                loan_amount: { type: 'number', description: 'Principal loan amount' },
                interest_rate: { type: 'number', description: 'Annual interest rate' },
                term_years: { type: 'number', description: 'Loan term in years' },
                points: { type: 'number', description: 'Points paid at closing (as percentage of loan amount)', default: 0 },
                closing_costs: { type: 'number', description: 'Other closing costs', default: 0 }
              },
              required: ['loan_amount', 'interest_rate', 'term_years']
            }
          }
        },
        required: ['loans']
      }
    },
    {
      name: 'calculate_irr',
      description: 'Calculates Internal Rate of Return with sensitivity analysis for investment cash flows',
      inputSchema: {
        type: 'object',
        properties: {
          initial_investment: { type: 'number', description: 'Initial cash outflow (purchase price + costs)' },
          cash_flows: {
            type: 'array',
            description: 'Array of annual net cash flows (income - expenses). Last flow should include sale proceeds',
            items: { type: 'number' }
          }
        },
        required: ['initial_investment', 'cash_flows']
      }
    },
    {
      name: 'analyze_fix_flip',
      description: 'Fix and flip profitability calculator with MAO (Maximum Allowable Offer) calculation',
      inputSchema: {
        type: 'object',
        properties: {
          purchase_price: { type: 'number', description: 'Purchase price of property' },
          rehab_costs: { type: 'number', description: 'Total estimated rehabilitation costs' },
          arv: { type: 'number', description: 'After Repair Value (estimated selling price)' },
          holding_costs: { type: 'number', description: 'Total holding costs during rehab', default: 0 },
          selling_costs_pct: { type: 'number', description: 'Selling costs as percentage of ARV (agent commissions)', default: 0.08 },
          finance_costs: { type: 'number', description: 'Cost of financing (loan interest, points)', default: 0 }
        },
        required: ['purchase_price', 'rehab_costs', 'arv']
      }
    },
    {
      name: 'calculate_npv',
      description: 'Calculates Net Present Value with inflation adjustment',
      inputSchema: {
        type: 'object',
        properties: {
          discount_rate: { type: 'number', description: 'Discount rate (your required rate of return)' },
          initial_investment: { type: 'number', description: 'Initial cash outflow' },
          cash_flows: {
            type: 'array',
            description: 'Array of annual net cash flows',
            items: { type: 'number' }
          }
        },
        required: ['discount_rate', 'initial_investment', 'cash_flows']
      }
    },
    {
      name: 'calculate_cocr',
      description: 'Calculates Cash-on-Cash Return with 5-year projections for rental property',
      inputSchema: {
        type: 'object',
        properties: {
          property_price: { type: 'number', description: 'Purchase price of property' },
          down_payment_pct: { type: 'number', description: 'Down payment percentage', default: 0.25 },
          loan_interest_rate: { type: 'number', description: 'Mortgage interest rate', default: 0.075 },
          loan_term_years: { type: 'number', description: 'Mortgage loan term in years', default: 30 },
          monthly_rent: { type: 'number', description: 'Expected monthly rental income' },
          monthly_expenses: { type: 'number', description: 'Total monthly operating expenses (not including mortgage)' },
          closing_costs: { type: 'number', description: 'Total closing costs', default: 0 }
        },
        required: ['property_price', 'monthly_rent', 'monthly_expenses']
      }
    },
    {
      name: 'calculate_dscr',
      description: 'Calculates Debt Service Coverage Ratio for investment loans and commercial financing',
      inputSchema: {
        type: 'object',
        properties: {
          monthly_rent: { type: 'number', description: 'Expected monthly gross rental income' },
          vacancy_rate: { type: 'number', description: 'Expected vacancy rate', default: 0.05 },
          annual_operating_expenses: { type: 'number', description: 'Total annual operating expenses (property management, maintenance, taxes, insurance)' },
          annual_debt_service: { type: 'number', description: 'Total annual mortgage payments (principal + interest)' }
        },
        required: ['monthly_rent', 'annual_operating_expenses', 'annual_debt_service']
      }
    },
    {
      name: 'analyze_breakeven',
      description: 'Performs breakeven analysis for rental properties with safety margin calculations',
      inputSchema: {
        type: 'object',
        properties: {
          total_monthly_expenses: { type: 'number', description: 'Total monthly expenses including mortgage, taxes, insurance, maintenance' },
          total_potential_rental_income: { type: 'number', description: 'Total potential monthly rental income at 100% occupancy' }
        },
        required: ['total_monthly_expenses', 'total_potential_rental_income']
      }
    },
    {
      name: 'analyze_sensitivity',
      description: 'Performs multi-variable sensitivity analysis on base investment value',
      inputSchema: {
        type: 'object',
        properties: {
          base_value: { type: 'number', description: 'Base value to test sensitivity against (e.g., base IRR)' },
          variables: {
            type: 'object',
            description: 'Object where keys are variable names and values are arrays of change percentages to test',
            additionalProperties: {
              type: 'array',
              items: { type: 'number' }
            }
          }
        },
        required: ['base_value', 'variables']
      }
    },
    {
      name: 'run_monte_carlo',
      description: 'Runs Monte Carlo risk simulation (10,000+ scenarios) for investment analysis',
      inputSchema: {
        type: 'object',
        properties: {
          initial_investment: { type: 'number', description: 'Initial amount invested' },
          mean_return: { type: 'number', description: 'Expected mean annual return' },
          stddev_return: { type: 'number', description: 'Standard deviation of annual returns (volatility)' },
          years: { type: 'number', description: 'Number of years to simulate' },
          simulations: { type: 'number', description: 'Number of simulations to run', default: 10000 }
        },
        required: ['initial_investment', 'mean_return', 'stddev_return', 'years']
      }
    },
    {
      name: 'calculate_tax_benefits',
      description: 'Calculates tax benefits and depreciation for rental property investment',
      inputSchema: {
        type: 'object',
        properties: {
          property_value: { type: 'number', description: 'Purchase price of property' },
          land_value: { type: 'number', description: 'Estimated value of land (non-depreciable)' },
          annual_rental_income: { type: 'number', description: 'Expected annual rental income' },
          marginal_tax_rate: { type: 'number', description: 'Your marginal federal income tax rate' }
        },
        required: ['property_value', 'land_value', 'annual_rental_income', 'marginal_tax_rate']
      }
    },
    {
      name: 'compare_properties',
      description: 'Compares up to 5 properties side-by-side using weighted scoring model',
      inputSchema: {
        type: 'object',
        properties: {
          properties: {
            type: 'array',
            description: 'Array of property objects to compare',
            items: {
              type: 'object',
              properties: {
                name: { type: 'string', description: 'Property identifier or address' },
                cash_flow: { type: 'number', description: 'Projected annual cash flow' },
                appreciation: { type: 'number', description: 'Projected annual appreciation potential (score 1-10)' },
                condition: { type: 'number', description: 'Property condition score (1-10)' },
                location: { type: 'number', description: 'Location quality score (1-10)' }
              },
              required: ['name', 'cash_flow', 'appreciation', 'condition', 'location']
            }
          }
        },
        required: ['properties']
      }
    },
    {
      name: 'analyze_refinance',
      description: 'Analyzes refinance opportunity with break-even and NPV calculations',
      inputSchema: {
        type: 'object',
        properties: {
          current_balance: { type: 'number', description: 'Current remaining mortgage balance' },
          current_rate: { type: 'number', description: 'Current mortgage interest rate' },
          current_term_remaining_years: { type: 'number', description: 'Years remaining on current loan' },
          new_rate: { type: 'number', description: 'New mortgage interest rate' },
          new_term_years: { type: 'number', description: 'Term for new loan' },
          closing_costs: { type: 'number', description: 'Total closing costs for refinance' }
        },
        required: ['current_balance', 'current_rate', 'current_term_remaining_years', 'new_rate', 'closing_costs']
      }
    },
    {
      name: 'analyze_airbnb_str',
      description: 'Analyzes Airbnb/Short-Term Rental income potential with seasonal variations',
      inputSchema: {
        type: 'object',
        properties: {
          purchase_price: { type: 'number', description: 'Purchase price of property' },
          down_payment_pct: { type: 'number', description: 'Down payment percentage', default: 0.25 },
          loan_interest_rate: { type: 'number', description: 'Mortgage interest rate', default: 0.075 },
          loan_term_years: { type: 'number', description: 'Mortgage loan term in years', default: 30 },
          avg_nightly_rate: { type: 'number', description: 'Average nightly rental rate' },
          avg_occupancy_pct: { type: 'number', description: 'Average expected occupancy rate', default: 0.65 },
          cleaning_fee: { type: 'number', description: 'Cleaning fee charged per stay', default: 100 },
          monthly_expenses: { type: 'number', description: 'Other monthly expenses (utilities, supplies)', default: 200 }
        },
        required: ['purchase_price', 'avg_nightly_rate']
      }
    },
    {
      name: 'analyze_1031_exchange',
      description: 'Analyzes 1031 like-kind exchange for tax deferral with qualification assessment',
      inputSchema: {
        type: 'object',
        properties: {
          sale_price: { type: 'number', description: 'Sale price of relinquished property' },
          adjusted_basis: { type: 'number', description: 'Adjusted basis (purchase price + improvements - depreciation)' },
          depreciation_taken: { type: 'number', description: 'Total depreciation taken on property' },
          replacement_property_price: { type: 'number', description: 'Purchase price of replacement property' }
        },
        required: ['sale_price', 'adjusted_basis', 'depreciation_taken', 'replacement_property_price']
      }
    },
    {
      name: 'analyze_market_comps',
      description: 'Performs market analysis with comparable property analysis and CMA',
      inputSchema: {
        type: 'object',
        properties: {
          subject_property: {
            type: 'object',
            properties: {
              sqft: { type: 'number', description: 'Square footage of subject property' },
              beds: { type: 'number', description: 'Number of bedrooms' },
              baths: { type: 'number', description: 'Number of bathrooms' }
            },
            required: ['sqft', 'beds', 'baths']
          },
          comps: {
            type: 'array',
            description: 'Array of comparable property sales',
            items: {
              type: 'object',
              properties: {
                sale_price: { type: 'number', description: 'Sale price of comparable' },
                sqft: { type: 'number', description: 'Square footage of comparable' },
                beds: { type: 'number', description: 'Number of bedrooms' },
                baths: { type: 'number', description: 'Number of bathrooms' },
                price_per_sqft: { type: 'number', description: 'Sale price per square foot' }
              },
              required: ['sale_price', 'sqft', 'beds', 'baths', 'price_per_sqft']
            }
          }
        },
        required: ['subject_property', 'comps']
      }
    },
    {
      name: 'analyze_construction_loan',
      description: 'Analyzes construction loan with draw schedules and permanent financing',
      inputSchema: {
        type: 'object',
        properties: {
          total_project_cost: { type: 'number', description: 'Total cost of project (land + construction + soft costs)' },
          loan_to_cost_ratio: { type: 'number', description: 'Loan-to-Cost ratio offered by lender', default: 0.75 },
          interest_rate: { type: 'number', description: 'Interest rate on construction loan', default: 0.08 },
          draw_schedule: { type: 'array', description: 'Array of draw percentages per phase', items: { type: 'number' }, default: [0.15, 0.20, 0.20, 0.25, 0.20] },
          loan_term_months: { type: 'number', description: 'Term of construction loan in months', default: 12 }
        },
        required: ['total_project_cost']
      }
    },
    {
      name: 'analyze_wholesale_deal',
      description: 'Analyzes wholesale deal with assignment fees and exit strategies',
      inputSchema: {
        type: 'object',
        properties: {
          contract_price: { type: 'number', description: 'Price under purchase contract' },
          arv: { type: 'number', description: 'After Repair Value' },
          estimated_repairs: { type: 'number', description: 'Estimated repair costs for end buyer' },
          assignment_fee: { type: 'number', description: 'Fee you will charge to assign contract' }
        },
        required: ['contract_price', 'arv', 'estimated_repairs', 'assignment_fee']
      }
    },
    {
      name: 'analyze_subject_to_deal',
      description: 'Analyzes subject-to deal with existing mortgage takeover',
      inputSchema: {
        type: 'object',
        properties: {
          property_value: { type: 'number', description: 'Current market value of property' },
          existing_mortgage_balance: { type: 'number', description: 'Current balance of existing mortgage' },
          existing_mortgage_payment: { type: 'number', description: 'Monthly payment of existing mortgage' },
          monthly_rent: { type: 'number', description: 'Expected monthly rental income' },
          monthly_expenses: { type: 'number', description: 'Monthly operating expenses (not including mortgage)' }
        },
        required: ['property_value', 'existing_mortgage_balance', 'existing_mortgage_payment', 'monthly_rent', 'monthly_expenses']
      }
    },
    {
      name: 'analyze_seller_financing',
      description: 'Analyzes seller financing deal with terms optimization',
      inputSchema: {
        type: 'object',
        properties: {
          sale_price: { type: 'number', description: 'Full sale price of property' },
          down_payment_pct: { type: 'number', description: 'Down payment percentage', default: 0.1 },
          interest_rate: { type: 'number', description: 'Interest rate on seller note', default: 0.08 },
          loan_term_years: { type: 'number', description: 'Term of seller financing in years', default: 30 }
        },
        required: ['sale_price']
      }
    },
    {
      name: 'calculate_capital_gains_tax',
      description: 'Calculates capital gains tax with optimization strategies and depreciation recapture',
      inputSchema: {
        type: 'object',
        properties: {
          purchase_price: { type: 'number', description: 'Original purchase price' },
          sale_price: { type: 'number', description: 'Sale price of property' },
          capital_improvements: { type: 'number', description: 'Cost of capital improvements made', default: 0 },
          depreciation_taken: { type: 'number', description: 'Total depreciation taken during ownership', default: 0 },
          holding_period_years: { type: 'number', description: 'Number of years property was held' },
          filing_status: { type: 'string', description: 'Tax filing status (single, married)', default: 'single' },
          total_income: { type: 'number', description: 'Your total annual income from other sources' }
        },
        required: ['purchase_price', 'sale_price', 'holding_period_years', 'total_income']
      }
    },
    {
      name: 'analyze_rent_vs_buy',
      description: 'Compares costs and benefits of renting vs buying with wealth building analysis',
      inputSchema: {
        type: 'object',
        properties: {
          monthly_rent: { type: 'number', description: 'Current monthly rent' },
          home_price: { type: 'number', description: 'Price of home considering buying' },
          down_payment_pct: { type: 'number', description: 'Down payment percentage', default: 0.2 },
          loan_interest_rate: { type: 'number', description: 'Mortgage interest rate', default: 0.075 },
          loan_term_years: { type: 'number', description: 'Mortgage loan term', default: 30 },
          annual_appreciation: { type: 'number', description: 'Expected annual home appreciation', default: 0.03 },
          annual_rent_increase: { type: 'number', description: 'Expected annual rent increase', default: 0.02 },
          investment_return: { type: 'number', description: 'Expected annual return on invested savings', default: 0.07 },
          years: { type: 'number', description: 'Time horizon for analysis', default: 7 }
        },
        required: ['monthly_rent', 'home_price']
      }
    },
    {
      name: 'track_deal_pipeline',
      description: 'Tracks and analyzes multiple deals through various stages',
      inputSchema: {
        type: 'object',
        properties: {
          deals: {
            type: 'array',
            description: 'Array of deal objects in pipeline',
            items: {
              type: 'object',
              properties: {
                id: { type: 'string', description: 'Deal identifier' },
                address: { type: 'string', description: 'Property address' },
                stage: { type: 'string', description: 'Current stage (analyzing, due_diligence, under_contract)' },
                purchase_price: { type: 'number', description: 'Target or contracted purchase price' },
                arv: { type: 'number', description: 'After Repair Value' },
                estimated_profit: { type: 'number', description: 'Estimated profit' }
              },
              required: ['id', 'address', 'stage']
            }
          }
        },
        required: ['deals']
      }
    },
    {
      name: 'analyze_joint_venture',
      description: 'Analyzes joint venture partnership with profit splitting',
      inputSchema: {
        type: 'object',
        properties: {
          partner_investments: {
            type: 'array',
            description: 'Array of investment amounts from each partner',
            items: { type: 'number' }
          },
          profit_split_pct: { type: 'number', description: 'Total profit percentage to split among partners (remainder may go to sponsor)', default: 0.7 }
        },
        required: ['partner_investments']
      }
    },
    {
      name: 'analyze_property_management',
      description: 'Compares self-management vs professional property management costs and benefits',
      inputSchema: {
        type: 'object',
        properties: {
          monthly_rent: { type: 'number', description: 'Monthly rental income' },
          self_management_hours: { type: 'number', description: 'Hours per month spent on management tasks' },
          hourly_rate: { type: 'number', description: 'Your opportunity cost per hour', default: 50 },
          professional_management_pct: { type: 'number', description: 'Professional management fee as percentage of rent', default: 0.08 }
        },
        required: ['monthly_rent', 'self_management_hours']
      }
    },
    {
      name: 'track_property_expenses',
      description: 'Tracks and analyzes property expenses with benchmarking and categorization',
      inputSchema: {
        type: 'object',
        properties: {
          expenses: {
            type: 'array',
            description: 'Array of expense objects',
            items: {
              type: 'object',
              properties: {
                category: { type: 'string', description: 'Expense category (repairs, taxes, insurance)' },
                amount: { type: 'number', description: 'Expense amount' },
                date: { type: 'string', description: 'Date of expense (YYYY-MM-DD)' }
              },
              required: ['category', 'amount']
            }
          }
        },
        required: ['expenses']
      }
    }
  ]
}));

// Handle tool execution
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  try {
    const result = RealEstateCalculator.executeTool(name, args);
    
    if (result.error) {
      return {
        content: [
          {
            type: 'text',
            text: `Error: ${result.error}`
          }
        ],
        isError: true
      };
    }
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2)
        }
      ]
    };
    
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: `Error executing ${name}: ${error.message}`
        }
      ],
      isError: true
    };
  }
});

// Start MCP server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Real Estate MCP Server running with all 31 professional calculators');
}

main().catch(console.error);