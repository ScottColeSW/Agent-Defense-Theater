const math = require('mathjs');

class RealEstateCalculator {

  // ===== BASIC ANALYSIS TOOLS =====

  static calculateAffordability(params) {
    try {
      const { annual_income, monthly_debts, savings, target_down_payment_pct = 0.2, annual_insurance_rate = 0.005, annual_tax_rate = 0.01, closing_costs_pct = 0.03, interest_rate = 0.075, loan_term_years = 30, max_back_end_dti = 0.43 } = params;
      const gross_monthly_income = annual_income / 12;
      const monthly_interest_rate = interest_rate / 12;
      const loan_term_months = loan_term_years * 12;
      const max_total_monthly_payment = (gross_monthly_income * max_back_end_dti) - monthly_debts;

      let estimated_home_price = Math.min(savings / (target_down_payment_pct + closing_costs_pct), (savings / target_down_payment_pct) * 0.8);
      let step = 10000;
      let foundSolution = false;
      let bestPrice = 0;

      for (let i = 0; i < 50; i++) {
        const down_payment = estimated_home_price * target_down_payment_pct;
        const loan_amount = estimated_home_price - down_payment;
        const monthly_pi = (loan_amount * monthly_interest_rate * Math.pow(1 + monthly_interest_rate, loan_term_months)) / (Math.pow(1 + monthly_interest_rate, loan_term_months) - 1);
        const monthly_ti = (estimated_home_price * (annual_tax_rate + annual_insurance_rate)) / 12;
        const estimated_piti = monthly_pi + monthly_ti;

        if (estimated_piti <= max_total_monthly_payment && down_payment + (estimated_home_price * closing_costs_pct) <= savings) {
          bestPrice = estimated_home_price;
          estimated_home_price += step;
          foundSolution = true;
        } else {
          step /= 2;
          estimated_home_price -= step;
        }
        if (step < 1) break;
      }

      if (!foundSolution) {
        return { error: "No affordable home found based on income, debts, and savings." };
      }

      const down_payment = bestPrice * target_down_payment_pct;
      const loan_amount = bestPrice - down_payment;
      const monthly_pi = (loan_amount * monthly_interest_rate * Math.pow(1 + monthly_interest_rate, loan_term_months)) / (Math.pow(1 + monthly_interest_rate, loan_term_months) - 1);
      const monthly_ti = (bestPrice * (annual_tax_rate + annual_insurance_rate)) / 12;
      const estimated_piti = monthly_pi + monthly_ti;
      const closing_costs = bestPrice * closing_costs_pct;
      const cash_needed = down_payment + closing_costs;
      const front_end_dti = estimated_piti / gross_monthly_income;
      const back_end_dti = (estimated_piti + monthly_debts) / gross_monthly_income;

      return {
        max_home_price: Math.round(bestPrice),
        max_loan_amount: Math.round(loan_amount),
        monthly_piti: Math.round(estimated_piti),
        cash_needed_at_closing: Math.round(cash_needed),
        front_end_dti: Math.round(front_end_dti * 10000) / 10000,
        back_end_dti: Math.round(back_end_dti * 10000) / 10000,
        down_payment_amount: Math.round(down_payment),
        closing_costs_estimate: Math.round(closing_costs)
      };
    } catch (error) {
      return { error: `Affordability calculation failed: ${error.message}` };
    }
  }

  static analyzeBrrrrDeal(params) {
    try {
      const { purchase_price, rehab_costs, arv, monthly_rent, refi_ltv = 0.75, refi_interest_rate = 0.075, refi_loan_term_years = 30, holding_costs = 0, closing_costs_purchase = 0, closing_costs_refi = 0, monthly_expense_pct = 0.35 } = params;
      const total_cash_invested = purchase_price + rehab_costs + holding_costs + closing_costs_purchase;
      const refi_loan_amount = arv * refi_ltv;
      const cash_out_refinance = refi_loan_amount - total_cash_invested;

      const monthly_interest_rate = refi_interest_rate / 12;
      const loan_term_months = refi_loan_term_years * 12;
      const monthly_mortgage = (refi_loan_amount * monthly_interest_rate * Math.pow(1 + monthly_interest_rate, loan_term_months)) / (Math.pow(1 + monthly_interest_rate, loan_term_months) - 1);
      const monthly_expenses = monthly_rent * monthly_expense_pct;
      const monthly_cash_flow = monthly_rent - monthly_mortgage - monthly_expenses;
      const annual_cash_flow = monthly_cash_flow * 12;

      const cocr = annual_cash_flow / total_cash_invested;
      const annual_roi = (annual_cash_flow + cash_out_refinance) / total_cash_invested;
      const mao = (arv * 0.7) - rehab_costs;

      return {
        total_investment: Math.round(total_cash_invested),
        cash_out_refinance: Math.round(cash_out_refinance),
        monthly_cash_flow: Math.round(monthly_cash_flow),
        annual_cash_flow: Math.round(annual_cash_flow),
        cash_on_cash_return: Math.round(cocr * 10000) / 10000,
        annual_roi: Math.round(annual_roi * 10000) / 10000,
        loan_amount_refi: Math.round(refi_loan_amount),
        monthly_mortgage_payment: Math.round(monthly_mortgage),
        maximum_allowable_offer: Math.round(mao),
        is_mao_compliant: purchase_price <= mao
      };
    } catch (error) {
      return { error: `BRRRR analysis failed: ${error.message}` };
    }
  }

  static evaluateHouseHack(params) {
    try {
      const { purchase_price, down_payment_pct = 0.25, interest_rate = 0.075, loan_term_years = 30, annual_taxes, annual_insurance, num_units, rent_owner_unit = 0, rent_other_units, vacancy_rate = 0.05, maintenance_rate = 0.1, market_rent_comparison } = params;
      const loan_amount = purchase_price * (1 - down_payment_pct);
      const monthly_interest_rate = interest_rate / 12;
      const loan_term_months = loan_term_years * 12;
      const monthly_pi = (loan_amount * monthly_interest_rate * Math.pow(1 + monthly_interest_rate, loan_term_months)) / (Math.pow(1 + monthly_interest_rate, loan_term_months) - 1);
      const monthly_ti = (annual_taxes + annual_insurance) / 12;

      const total_rental_income = (rent_owner_unit + (rent_other_units * (num_units - 1))) * (1 - vacancy_rate);
      const monthly_maintenance = (rent_other_units * num_units) * maintenance_rate;
      const total_monthly_cost = monthly_pi + monthly_ti + monthly_maintenance;
      const effective_housing_cost = total_monthly_cost - total_rental_income;
      const monthly_savings_vs_rent = market_rent_comparison - effective_housing_cost;

      return {
        effective_housing_cost: Math.round(effective_housing_cost),
        monthly_savings_vs_rent: Math.round(monthly_savings_vs_rent),
        annual_savings: Math.round(monthly_savings_vs_rent * 12),
        total_rental_income: Math.round(total_rental_income),
        total_monthly_cost: Math.round(total_monthly_cost)
      };
    } catch (error) {
      return { error: `House hack evaluation failed: ${error.message}` };
    }
  }

  static projectPortfolioGrowth(params) {
  try {
      const { initial_capital, annual_savings, acquisition_frequency_months, avg_property_price, avg_down_payment_pct = 0.25, avg_cocr = 0.08, appreciation_rate = 0.03, hold_period_years = 20 } = params;

      // Then do validation with properly defined variables
      const downPaymentRequired = avg_property_price * avg_down_payment_pct;
      const maxSavingsAvailable = initial_capital + (annual_savings * hold_period_years);
      
      if (maxSavingsAvailable < downPaymentRequired) {
          return {
              error: "Insufficient capital for property acquisition",
              required_down_payment: downPaymentRequired,
              available_capital: maxSavingsAvailable
          };
      }

      let cash = initial_capital;
      const properties = [];
      const results = { equity: [initial_capital], cash_flow: [0] };

      for (let month = 0; month <= hold_period_years * 12; month++) {
        if (month % 12 === 0 && month > 0) cash += annual_savings;

        if (month % acquisition_frequency_months === 0 && month > 0) {
          const down_payment_needed = avg_property_price * avg_down_payment_pct;
          if (cash >= down_payment_needed) {
            cash -= down_payment_needed;
            properties.push({
              purchase_price: avg_property_price,
              equity: down_payment_needed,
              value: avg_property_price
            });
          }
        }

        let total_equity = cash;
        let annual_cash_flow = 0;
        for (const prop of properties) {
          prop.value *= (1 + (appreciation_rate / 12));
          prop.equity = prop.value - (prop.purchase_price * (1 - avg_down_payment_pct));
          total_equity += prop.equity;
          annual_cash_flow += (prop.purchase_price * avg_down_payment_pct) * avg_cocr;
        }
        if (month % 12 === 0) {
          results.equity.push(Math.round(total_equity));
          results.cash_flow.push(Math.round(annual_cash_flow));
        }
      }

      return {
        number_of_properties: properties.length,
        total_equity: results.equity[results.equity.length - 1],
        annual_passive_income: results.cash_flow[results.cash_flow.length - 1],
        equity_projections: results.equity,
        cash_flow_projections: results.cash_flow
      };
    } catch (error) {
      return { error: `Portfolio projection failed: ${error.message}` };
    }
  }

  static analyzeSyndication(params) {
    try {
      const { investment, preferred_return_pct = 0.08, sponsor_split_pct = 0.3, projected_irr = 0.15, hold_period = 5, exit_value } = params;
      const preferred_return_annual = investment * preferred_return_pct;
      const total_preferred_return = preferred_return_annual * hold_period;
      let investor_profit = 0;
      let sponsor_profit = 0;

      if (exit_value) {
        const total_profit = exit_value - investment;
        investor_profit = total_profit * (1 - sponsor_split_pct);
        sponsor_profit = total_profit * sponsor_split_pct;
      } else {
        investor_profit = (investment * Math.pow(1 + projected_irr, hold_period)) - investment - total_preferred_return;
        sponsor_profit = investor_profit * (sponsor_split_pct / (1 - sponsor_split_pct));
      }

      const total_investor_return = investment + total_preferred_return + investor_profit;
      const equity_multiple = total_investor_return / investment;
      const avg_annual_cocr = (Math.pow(equity_multiple, 1 / hold_period) - 1);

      return {
        total_projected_return: Math.round(total_investor_return),
        equity_multiple: Math.round(equity_multiple * 100) / 100,
        average_annual_cocr: Math.round(avg_annual_cocr * 10000) / 10000,
        investor_profit: Math.round(investor_profit),
        sponsor_profit: Math.round(sponsor_profit),
        preferred_return_earned: Math.round(total_preferred_return)
      };
    } catch (error) {
      return { error: `Syndication analysis failed: ${error.message}` };
    }
  }

  // ===== LENDING & QUALIFICATION TOOLS =====

  static calculateMortgageAffordability(params) {
    return this.calculateAffordability(params);
  }

  static analyzeDebtToIncome(params) {
    try {
      const { gross_monthly_income, total_monthly_debts, proposed_monthly_piti } = params;
      const current_dti = total_monthly_debts / gross_monthly_income;
      const proposed_dti = (total_monthly_debts + proposed_monthly_piti) / gross_monthly_income;

      const qualification = {
        conventional: proposed_dti <= 0.45,
        fha: proposed_dti <= 0.57,
        va: proposed_dti <= 0.41,
        usda: proposed_dti <= 0.41,
        jumbo: proposed_dti <= 0.35
      };

      return {
        current_dti: Math.round(current_dti * 10000) / 10000,
        proposed_dti: Math.round(proposed_dti * 10000) / 10000,
        qualification
      };
    } catch (error) {
      return { error: `DTI analysis failed: ${error.message}` };
    }
  }

  static compareLoans(params) {
    try {
      const { loans } = params;
      const results = loans.map(loan => {
        const { loan_amount, interest_rate, term_years, points = 0, closing_costs = 0 } = loan;
        const monthly_rate = interest_rate / 12;
        const months = term_years * 12;
        const monthly_payment = (loan_amount * monthly_rate * Math.pow(1 + monthly_rate, months)) / (Math.pow(1 + monthly_rate, months) - 1);
        const total_interest = (monthly_payment * months) - loan_amount;
        const points_cost = loan_amount * (points / 100);
        const total_cost = loan_amount + total_interest + points_cost + closing_costs;

        return {
          monthly_payment: Math.round(monthly_payment),
          total_interest: Math.round(total_interest),
          total_cost: Math.round(total_cost),
          points_cost: Math.round(points_cost),
          apr: Math.round((Math.pow((monthly_payment * months) / (loan_amount - points_cost - closing_costs), 1 / term_years) - 1) * 10000) / 10000
        };
      });

      return { comparisons: results };
    } catch (error) {
      return { error: `Loan comparison failed: ${error.message}` };
    }
  }

  // ===== INVESTMENT ANALYSIS TOOLS =====

  static calculateIrr(params) {
    try {
      const { initial_investment, cash_flows } = params;
      const all_cash_flows = [-initial_investment, ...cash_flows];
      
      // Newton-Raphson method for IRR calculation
      function calculateIRR(cashFlows, guess = 0.1) {
        const maxIterations = 100;
        const tolerance = 1e-6;
        
        for (let i = 0; i < maxIterations; i++) {
          let npv = 0;
          let dnpv = 0;
          
          for (let t = 0; t < cashFlows.length; t++) {
            const factor = Math.pow(1 + guess, t);
            npv += cashFlows[t] / factor;
            dnpv -= t * cashFlows[t] / (factor * (1 + guess));
          }
          
          if (Math.abs(npv) < tolerance) {
            return guess;
          }
          
          if (Math.abs(dnpv) < tolerance) {
            throw new Error("Derivative too small");
          }
          
          guess = guess - npv / dnpv;
        }
        
        throw new Error("IRR calculation did not converge");
      }
      
      const irr = calculateIRR(all_cash_flows);
      return { internal_rate_of_return: Math.round(irr * 10000) / 10000 };
    } catch (error) {
      return { error: `IRR calculation failed: ${error.message}` };
    }
  }

  static analyzeFixFlip(params) {
    try {
      const { purchase_price, rehab_costs, arv, holding_costs = 0, selling_costs_pct = 0.08, finance_costs = 0 } = params;
      const total_investment = purchase_price + rehab_costs + holding_costs + finance_costs;
      const sale_proceeds = arv * (1 - selling_costs_pct);
      const net_profit = sale_proceeds - total_investment;
      const roi = net_profit / total_investment;
      const profit_margin = net_profit / arv;
      const mao = (arv * 0.7) - rehab_costs;

      return {
        total_investment: Math.round(total_investment),
        net_profit: Math.round(net_profit),
        roi: Math.round(roi * 10000) / 10000,
        profit_margin: Math.round(profit_margin * 10000) / 10000,
        maximum_allowable_offer: Math.round(mao),
        is_mao_compliant: purchase_price <= mao
      };
    } catch (error) {
      return { error: `Fix & Flip analysis failed: ${error.message}` };
    }
  }

  static calculateNpv(params) {
    try {
      const { discount_rate, initial_investment, cash_flows } = params;
      let npv = -initial_investment;
      for (let t = 0; t < cash_flows.length; t++) {
        npv += cash_flows[t] / Math.pow(1 + discount_rate, t + 1);
      }
      return { net_present_value: Math.round(npv) };
    } catch (error) {
      return { error: `NPV calculation failed: ${error.message}` };
    }
  }

  static calculateCocr(params) {
    try {
      const { property_price, down_payment_pct = 0.25, loan_interest_rate = 0.075, loan_term_years = 30, monthly_rent, monthly_expenses, closing_costs = 0 } = params;
      const down_payment = property_price * down_payment_pct;
      const loan_amount = property_price - down_payment;
      const monthly_rate = loan_interest_rate / 12;
      const months = loan_term_years * 12;
      const monthly_mortgage = (loan_amount * monthly_rate * Math.pow(1 + monthly_rate, months)) / (Math.pow(1 + monthly_rate, months) - 1);
      const monthly_cash_flow = monthly_rent - monthly_mortgage - monthly_expenses;
      const total_cash_invested = down_payment + closing_costs;
      const annual_cash_flow = monthly_cash_flow * 12;
      const cocr = annual_cash_flow / total_cash_invested;

      return {
        cash_on_cash_return: Math.round(cocr * 10000) / 10000,
        annual_cash_flow: Math.round(annual_cash_flow),
        monthly_cash_flow: Math.round(monthly_cash_flow),
        total_cash_invested: Math.round(total_cash_invested)
      };
    } catch (error) {
      return { error: `CoC calculation failed: ${error.message}` };
    }
  }

  static calculateDscr(params) {
    try {
      const { monthly_rent, vacancy_rate = 0.05, annual_operating_expenses, annual_debt_service } = params;
      const annual_gross_rent = monthly_rent * 12;
      const effective_annual_rent = annual_gross_rent * (1 - vacancy_rate);
      const annual_noi = effective_annual_rent - annual_operating_expenses;
      const dscr = annual_noi / annual_debt_service;
      const min_noi = annual_debt_service * 1.0;
      const min_rent = (min_noi + annual_operating_expenses) / (12 * (1 - vacancy_rate));

      return {
        debt_service_coverage_ratio: Math.round(dscr * 100) / 100,
        net_operating_income: Math.round(annual_noi),
        minimum_rent_for_approval: Math.round(min_rent)
      };
    } catch (error) {
      return { error: `DSCR calculation failed: ${error.message}` };
    }
  }

  static analyzeBreakeven(params) {
    try {
      const { total_monthly_expenses, total_potential_rental_income } = params;
      const breakeven_occupancy_pct = total_monthly_expenses / total_potential_rental_income;
      const safety_margin_pct = 1 - breakeven_occupancy_pct;

      return {
        breakeven_occupancy_pct: Math.round(breakeven_occupancy_pct * 10000) / 10000,
        safety_margin_pct: Math.round(safety_margin_pct * 10000) / 10000,
        breakeven_occupancy_units: Math.ceil(breakeven_occupancy_pct * 100) // Assuming 100 units for scale
      };
    } catch (error) {
      return { error: `Breakeven analysis failed: ${error.message}` };
    }
  }

  // ===== ADVANCED ANALYSIS TOOLS =====
  // Note: Many advanced tools are simulations. These are simplified implementations.

  static analyzeSensitivity(params) {
    try {
      const { base_value, variables } = params;
      const results = {};
      for (const [key, values] of Object.entries(variables)) {
        results[key] = values.map(value => ({ change: value, result: base_value * (1 + value) }));
      }
      return { sensitivity_analysis: results };
    } catch (error) {
      return { error: `Sensitivity analysis failed: ${error.message}` };
    }
  }

  static runMonteCarlo(params) {
    try {
      const { initial_investment, mean_return, stddev_return, years, simulations = 1000 } = params;
      const results = [];
      
      // ADT change: a seeded generator (mulberry32) in place of Math.random, so the same call gives the same answer and runs repeat.
      let seedState = (params.seed ?? 1) >>> 0;
      const rand = () => { seedState = (seedState + 0x6D2B79F5) >>> 0; let t = seedState; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
      // Box-Muller transform for normal distribution
      function normalRandom(mean = 0, stddev = 1) {
        let u = 0, v = 0;
        while(u === 0) u = rand(); // Converting [0,1) to (0,1)
        while(v === 0) v = rand();
        const z = Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
        return z * stddev + mean;
      }
      
      for (let i = 0; i < simulations; i++) {
        let value = initial_investment;
        for (let y = 0; y < years; y++) {
          const return_rate = normalRandom(mean_return, stddev_return);
          value *= (1 + return_rate);
        }
        results.push(value);
      }
      
      results.sort((a, b) => a - b);
      const median = results[Math.floor(simulations / 2)];
      const percentile5 = results[Math.floor(simulations * 0.05)];
      const percentile95 = results[Math.floor(simulations * 0.95)];

      return {
        median_final_value: Math.round(median),
        fifth_percentile: Math.round(percentile5),
        ninety_fifth_percentile: Math.round(percentile95),
        probability_of_loss: Math.round((results.filter(v => v < initial_investment).length / simulations) * 10000) / 10000
      };
    } catch (error) {
      return { error: `Monte Carlo simulation failed: ${error.message}` };
    }
  }

  static calculateTaxBenefits(params) {
    try {
      const { property_value, land_value, annual_rental_income, marginal_tax_rate } = params;
      const depreciable_basis = property_value - land_value;
      const annual_depreciation = depreciable_basis / 27.5;
      const annual_tax_savings = annual_depreciation * marginal_tax_rate;

      return {
        annual_depreciation: Math.round(annual_depreciation),
        annual_tax_savings: Math.round(annual_tax_savings),
        taxable_rental_income: Math.round(annual_rental_income - annual_depreciation)
      };
    } catch (error) {
      return { error: `Tax benefit calculation failed: ${error.message}` };
    }
  }

  static compareProperties(params) {
    try {
      const { properties } = params;
      const scores = properties.map(prop => {
        const score = (prop.cash_flow * 0.4) + (prop.appreciation * 0.3) + (prop.condition * 0.2) + (prop.location * 0.1);
        return { ...prop, score: Math.round(score * 100) / 100 };
      });
      scores.sort((a, b) => b.score - a.score);
      return { ranked_properties: scores };
    } catch (error) {
      return { error: `Property comparison failed: ${error.message}` };
    }
  }

  static analyzeRefinance(params) {
    try {
      const { current_balance, current_rate, current_term_remaining_years, new_rate, new_term_years, closing_costs } = params;
      const monthly_rate_old = current_rate / 12;
      const months_old = current_term_remaining_years * 12;
      const old_payment = (current_balance * monthly_rate_old * Math.pow(1 + monthly_rate_old, months_old)) / (Math.pow(1 + monthly_rate_old, months_old) - 1);
      const total_old_interest = (old_payment * months_old) - current_balance;

      const monthly_rate_new = new_rate / 12;
      const months_new = new_term_years * 12;
      const new_payment = (current_balance * monthly_rate_new * Math.pow(1 + monthly_rate_new, months_new)) / (Math.pow(1 + monthly_rate_new, months_new) - 1);
      const total_new_interest = (new_payment * months_new) - current_balance;

      const monthly_savings = old_payment - new_payment;
      const break_even_months = closing_costs / monthly_savings;

      return {
        current_monthly_payment: Math.round(old_payment),
        new_monthly_payment: Math.round(new_payment),
        monthly_savings: Math.round(monthly_savings),
        total_interest_savings: Math.round(total_old_interest - total_new_interest),
        break_even_months: Math.round(break_even_months)
      };
    } catch (error) {
      return { error: `Refinance analysis failed: ${error.message}` };
    }
  }

  static analyzeAirbnbStr(params) {
    try {
      // Add JavaScript defaults as fallbacks to the schema defaults
      const { 
        purchase_price, 
        down_payment_pct = 0.25, 
        loan_interest_rate = 0.075, 
        loan_term_years = 30, 
        avg_nightly_rate, 
        avg_occupancy_pct = 0.65, 
        cleaning_fee = 100, 
        monthly_expenses = 200 
      } = params;

      const gross_annual_revenue = (avg_nightly_rate * 365 * avg_occupancy_pct) + (cleaning_fee * 365 * avg_occupancy_pct);
      const down_payment = purchase_price * down_payment_pct;
      const loan_amount = purchase_price - down_payment;
      const monthly_rate = loan_interest_rate / 12;
      const months = loan_term_years * 12;
      const monthly_mortgage = (loan_amount * monthly_rate * Math.pow(1 + monthly_rate, months)) / (Math.pow(1 + monthly_rate, months) - 1);
      const annual_mortgage = monthly_mortgage * 12;
      const annual_cash_flow = gross_annual_revenue - monthly_expenses * 12 - annual_mortgage;
      const total_cash_invested = down_payment;
      const cocr = annual_cash_flow / total_cash_invested;

      return {
        gross_annual_revenue: Math.round(gross_annual_revenue),
        annual_cash_flow: Math.round(annual_cash_flow),
        cash_on_cash_return: Math.round(cocr * 10000) / 10000,
        break_even_occupancy: Math.round((annual_mortgage + (monthly_expenses * 12)) / (avg_nightly_rate * 365 + cleaning_fee * 365) * 10000) / 10000
      };
    } catch (error) {
      return { error: `Airbnb analysis failed: ${error.message}` };
    }
  }

  static analyze1031Exchange(params) {
    try {
      const { sale_price, adjusted_basis, depreciation_taken, replacement_property_price } = params;
      const taxable_gain = sale_price - adjusted_basis;
      const depreciation_recapture_tax = depreciation_taken * 0.25;
      const capital_gain_tax = (taxable_gain - depreciation_taken) * 0.15;
      const total_tax_liability = depreciation_recapture_tax + capital_gain_tax;
      const net_proceeds = sale_price - total_tax_liability;
      const equity_reinvestment_requirement = net_proceeds;
      const boot = replacement_property_price < equity_reinvestment_requirement ? equity_reinvestment_requirement - replacement_property_price : 0;

      return {
        taxable_gain: Math.round(taxable_gain),
        total_tax_liability: Math.round(total_tax_liability),
        net_proceeds: Math.round(net_proceeds),
        boot: Math.round(boot),
        qualifies: replacement_property_price >= net_proceeds && boot === 0
      };
    } catch (error) {
      return { error: `1031 exchange analysis failed: ${error.message}` };
    }
  }

  static analyzeMarketComps(params) {
    try {
      const { subject_property, comps } = params;
      const adjusted_values = comps.map(comp => {
        let adjustment = comp.sale_price;
        adjustment += (subject_property.sqft - comp.sqft) * comp.price_per_sqft;
        adjustment += (subject_property.beds - comp.beds) * 5000;
        adjustment += (subject_property.baths - comp.baths) * 3000;
        return adjustment;
      });
      const estimated_value = adjusted_values.reduce((sum, val) => sum + val, 0) / adjusted_values.length;
      return {
        estimated_market_value: Math.round(estimated_value),
        price_per_sqft: Math.round(estimated_value / subject_property.sqft),
        comps_used: comps.length
      };
    } catch (error) {
      return { error: `Market comp analysis failed: ${error.message}` };
    }
  }

  static analyzeConstructionLoan(params) {
    try {
      const { total_project_cost, loan_to_cost_ratio = 0.75, interest_rate, draw_schedule, loan_term_months } = params;
      const loan_amount = total_project_cost * loan_to_cost_ratio;
      const equity_required = total_project_cost - loan_amount;
      const total_interest = loan_amount * interest_rate * (loan_term_months / 12);
      const total_project_cost_with_finance = total_project_cost + total_interest;

      return {
        loan_amount: Math.round(loan_amount),
        equity_required: Math.round(equity_required),
        total_interest: Math.round(total_interest),
        total_project_cost_with_finance: Math.round(total_project_cost_with_finance)
      };
    } catch (error) {
      return { error: `Construction loan analysis failed: ${error.message}` };
    }
  }

  static analyzeWholesaleDeal(params) {
    try {
      const { contract_price, arv, estimated_repairs, assignment_fee } = params;
      const mao = (arv * 0.7) - estimated_repairs;
      const buyer_price = contract_price + assignment_fee;
      const buyer_profit = arv - buyer_price - estimated_repairs;
      const buyer_roi = buyer_profit / (buyer_price + estimated_repairs);
      const wholesale_fee = assignment_fee;

      return {
        maximum_allowable_offer: Math.round(mao),
        buyer_acquisition_cost: Math.round(buyer_price),
        buyer_profit: Math.round(buyer_profit),
        buyer_roi: Math.round(buyer_roi * 10000) / 10000,
        wholesale_fee: Math.round(wholesale_fee),
        deal_viable: contract_price <= mao
      };
    } catch (error) {
      return { error: `Wholesale deal analysis failed: ${error.message}` };
    }
  }

  static analyzeSubjectToDeal(params) {
    try {
      const { property_value, existing_mortgage_balance, existing_mortgage_payment, monthly_rent, monthly_expenses } = params;
      const instant_equity = property_value - existing_mortgage_balance;
      const monthly_cash_flow = monthly_rent - existing_mortgage_payment - monthly_expenses;
      const annual_cash_flow = monthly_cash_flow * 12;
      const cocr = annual_cash_flow / instant_equity;

      return {
        instant_equity: Math.round(instant_equity),
        monthly_cash_flow: Math.round(monthly_cash_flow),
        annual_cash_flow: Math.round(annual_cash_flow),
        cash_on_cash_return: Math.round(cocr * 10000) / 10000
      };
    } catch (error) {
      return { error: `Subject-to analysis failed: ${error.message}` };
    }
  }

  static analyzeSellerFinancing(params) {
    try {
      const { sale_price, down_payment_pct = 0.1, interest_rate = 0.08, loan_term_years = 30 } = params;
      const loan_amount = sale_price * (1 - down_payment_pct);
      const monthly_rate = interest_rate / 12;
      const months = loan_term_years * 12;
      const monthly_payment = (loan_amount * monthly_rate * Math.pow(1 + monthly_rate, months)) / (Math.pow(1 + monthly_rate, months) - 1);
      const total_interest = (monthly_payment * months) - loan_amount;

      return {
        loan_amount: Math.round(loan_amount),
        monthly_payment: Math.round(monthly_payment),
        total_interest: Math.round(total_interest),
        total_payments: Math.round(monthly_payment * months)
      };
    } catch (error) {
      return { error: `Seller financing analysis failed: ${error.message}` };
    }
  }

  static calculateCapitalGainsTax(params) {
    try {
      const { purchase_price, sale_price, capital_improvements, depreciation_taken, holding_period_years, filing_status, total_income } = params;
      const adjusted_basis = purchase_price + capital_improvements - depreciation_taken;
      const taxable_gain = sale_price - adjusted_basis;
      const is_long_term = holding_period_years >= 1;
      // Ensure default values are properly set
      const improvements = capital_improvements || 0;
      const depreciation = depreciation_taken || 0;
      let tax_rate = 0.15;

      if (is_long_term) {
        if (filing_status === 'single' && total_income + taxable_gain > 492300) tax_rate = 0.20;
        if (filing_status === 'married' && total_income + taxable_gain > 553850) tax_rate = 0.20;
      } else {
        tax_rate = 0.22;
      }

      const depreciation_recapture_tax = depreciation_taken * 0.25;
      const capital_gains_tax = (taxable_gain - depreciation_taken) * tax_rate;
      const total_tax = depreciation_recapture_tax + capital_gains_tax;

      return {
        taxable_gain: Math.round(taxable_gain),
        depreciation_recapture_tax: Math.round(depreciation_recapture_tax),
        capital_gains_tax: Math.round(capital_gains_tax),
        total_tax_liability: Math.round(total_tax),
        net_proceeds: Math.round(sale_price - total_tax)
      };
    } catch (error) {
      return { error: `Capital gains tax calculation failed: ${error.message}` };
    }
  }

  static analyzeRentVsBuy(params) {
      try {
          const { 
              monthly_rent, 
              home_price, 
              down_payment_pct = 0.2, 
              loan_interest_rate = 0.075, 
              loan_term_years = 30, 
              annual_appreciation = 0.03, 
              annual_rent_increase = 0.02, 
              investment_return = 0.07, 
              years = 7
          } = params;

          const down_payment = home_price * down_payment_pct;
          const loan_amount = home_price - down_payment;
          const monthly_rate = loan_interest_rate / 12;
          const total_months = loan_term_years * 12;
          const monthly_investment_return = investment_return / 12;
          
          // Calculate monthly mortgage payment (Principal & Interest)
          const monthly_mortgage = loan_amount * (monthly_rate * Math.pow(1 + monthly_rate, total_months)) / (Math.pow(1 + monthly_rate, total_months) - 1);
          
          // Estimate other homeowner costs (taxes, insurance, maintenance = ~2% annually)
          const monthly_other_costs = (home_price * 0.02) / 12;
          const total_monthly_homeowner_cost = monthly_mortgage + monthly_other_costs;

          let cumulative_rent_paid = 0;
          let cumulative_homeowner_payments = 0;
          let remaining_loan_balance = loan_amount;
          let renter_investment_balance = down_payment; // Renter invests down payment initially
          
          // Month-by-month analysis for accurate investment compounding
          for (let year = 1; year <= years; year++) {
              for (let month = 1; month <= 12; month++) {
                  // Calculate current month's rent (with annual increases applied at start of each year)
                  const current_monthly_rent = monthly_rent * Math.pow(1 + annual_rent_increase, year - 1);
                  cumulative_rent_paid += current_monthly_rent;
                  
                  // Calculate homeowner payments
                  cumulative_homeowner_payments += total_monthly_homeowner_cost;
                  
                  // Calculate mortgage principal paydown for this month
                  const interest_payment = remaining_loan_balance * monthly_rate;
                  const principal_payment = monthly_mortgage - interest_payment;
                  remaining_loan_balance = Math.max(0, remaining_loan_balance - principal_payment);
                  
                  // Apply monthly investment return to renter's existing balance first
                  renter_investment_balance = renter_investment_balance * (1 + monthly_investment_return);
                  
                  // Then add/subtract monthly cash flow difference
                  const monthly_cash_flow_difference = total_monthly_homeowner_cost - current_monthly_rent;
                  renter_investment_balance += monthly_cash_flow_difference;
                  
                  // Ensure investment balance doesn't go below zero (renter can't borrow against investments)
                  renter_investment_balance = Math.max(0, renter_investment_balance);
              }
          }

          // Calculate final positions
          const final_home_value = home_price * Math.pow(1 + annual_appreciation, years);
          const home_equity = final_home_value - remaining_loan_balance;
          const total_buy_cost = down_payment + cumulative_homeowner_payments;

          // Net worth comparison
          const homeowner_net_worth = home_equity;
          const renter_net_worth = renter_investment_balance;

          // Calculate break-even year with month-by-month precision
          let break_even_year = "Not reached";
          let temp_loan_balance = loan_amount;
          let temp_renter_balance = down_payment;
          
          for (let year = 1; year <= years; year++) {
              for (let month = 1; month <= 12; month++) {
                  // Simulate loan paydown for this month
                  const interest_payment = temp_loan_balance * monthly_rate;
                  const principal_payment = monthly_mortgage - interest_payment;
                  temp_loan_balance = Math.max(0, temp_loan_balance - principal_payment);
                  
                  // Simulate renter investments for this month
                  const current_monthly_rent = monthly_rent * Math.pow(1 + annual_rent_increase, year - 1);
                  
                  // Apply monthly return to existing balance
                  temp_renter_balance = temp_renter_balance * (1 + monthly_investment_return);
                  
                  // Add monthly cash flow difference
                  const monthly_difference = total_monthly_homeowner_cost - current_monthly_rent;
                  temp_renter_balance += monthly_difference;
                  temp_renter_balance = Math.max(0, temp_renter_balance);
              }
              
              // Check if homeowner net worth exceeds renter net worth at year end
              const temp_home_value = home_price * Math.pow(1 + annual_appreciation, year);
              const temp_home_equity = temp_home_value - temp_loan_balance;
              
              if (temp_home_equity >= temp_renter_balance && break_even_year === "Not reached") {
                  break_even_year = year;
                  break;
              }
          }

          return {
              total_rent_cost: Math.round(cumulative_rent_paid),
              total_buy_cost: Math.round(total_buy_cost),
              home_equity: Math.round(home_equity),
              investment_balance: Math.round(renter_investment_balance),
              net_worth_buy: Math.round(homeowner_net_worth),
              net_worth_rent: Math.round(renter_net_worth),
              break_even_year: break_even_year,
              monthly_mortgage_payment: Math.round(monthly_mortgage),
              monthly_total_homeowner_cost: Math.round(total_monthly_homeowner_cost)
          };
          
      } catch (error) {
          return { error: `Rent vs Buy analysis failed: ${error.message}` };
      }
  }

  static trackDealPipeline(params) {
    try {
      const { deals } = params;
      const stages = {};
      deals.forEach(deal => {
        if (!stages[deal.stage]) stages[deal.stage] = [];
        stages[deal.stage].push(deal);
      });
      return { pipeline: stages };
    } catch (error) {
      return { error: `Deal pipeline tracking failed: ${error.message}` };
    }
  }

  static analyzeJointVenture(params) {
    try {
      const { partner_investments, profit_split_pct } = params;
      const total_investment = partner_investments.reduce((sum, inv) => sum + inv, 0);
      const splits = partner_investments.map(inv => ({
        investment: inv,
        share: inv / total_investment,
        profit_share: (inv / total_investment) * profit_split_pct
      }));
      return { joint_venture_splits: splits };
    } catch (error) {
      return { error: `Joint venture analysis failed: ${error.message}` };
    }
  }

  static analyzePropertyManagement(params) {
    try {
      const { monthly_rent, self_management_hours, hourly_rate, professional_management_pct = 0.08 } = params;
      const professional_cost = monthly_rent * professional_management_pct;
      const self_management_cost = self_management_hours * hourly_rate;
      const savings = self_management_cost - professional_cost;

      return {
        professional_management_cost: Math.round(professional_cost),
        self_management_cost: Math.round(self_management_cost),
        monthly_savings: Math.round(savings),
        recommended_option: savings > 0 ? 'Professional' : 'Self'
      };
    } catch (error) {
      return { error: `Property management analysis failed: ${error.message}` };
    }
  }

  static trackPropertyExpenses(params) {
    try {
      const { expenses } = params;
      const categories = {};
      let total = 0;
      expenses.forEach(exp => {
        if (!categories[exp.category]) categories[exp.category] = 0;
        categories[exp.category] += exp.amount;
        total += exp.amount;
      });
      return { expenses_by_category: categories, total_expenses: Math.round(total) };
    } catch (error) {
      return { error: `Expense tracking failed: ${error.message}` };
    }
  }

  // ===== MAIN DISPATCH FUNCTION =====

  static executeTool(toolName, params) {
    const methodMap = {
      'calculate_affordability': this.calculateAffordability,
      'analyze_brrrr_deal': this.analyzeBrrrrDeal,
      'evaluate_house_hack': this.evaluateHouseHack,
      'project_portfolio_growth': this.projectPortfolioGrowth,
      'analyze_syndication': this.analyzeSyndication,
      'calculate_mortgage_affordability': this.calculateMortgageAffordability,
      'analyze_debt_to_income': this.analyzeDebtToIncome,
      'compare_loans': this.compareLoans,
      'calculate_irr': this.calculateIrr,
      'analyze_fix_flip': this.analyzeFixFlip,
      'calculate_npv': this.calculateNpv,
      'calculate_cocr': this.calculateCocr,
      'calculate_dscr': this.calculateDscr,
      'analyze_breakeven': this.analyzeBreakeven,
      'analyze_sensitivity': this.analyzeSensitivity,
      'run_monte_carlo': this.runMonteCarlo,
      'calculate_tax_benefits': this.calculateTaxBenefits,
      'compare_properties': this.compareProperties,
      'analyze_refinance': this.analyzeRefinance,
      'analyze_airbnb_str': this.analyzeAirbnbStr,
      'analyze_1031_exchange': this.analyze1031Exchange,
      'analyze_market_comps': this.analyzeMarketComps,
      'analyze_construction_loan': this.analyzeConstructionLoan,
      'analyze_wholesale_deal': this.analyzeWholesaleDeal,
      'analyze_subject_to_deal': this.analyzeSubjectToDeal,
      'analyze_seller_financing': this.analyzeSellerFinancing,
      'calculate_capital_gains_tax': this.calculateCapitalGainsTax,
      'analyze_rent_vs_buy': this.analyzeRentVsBuy,
      'track_deal_pipeline': this.trackDealPipeline,
      'analyze_joint_venture': this.analyzeJointVenture,
      'analyze_property_management': this.analyzePropertyManagement,
      'track_property_expenses': this.trackPropertyExpenses
    };

    const method = methodMap[toolName];
    if (!method) {
      throw new Error(`Tool '${toolName}' not found.`);
    }
    return method.call(this, params);
  }
}

module.exports = RealEstateCalculator;