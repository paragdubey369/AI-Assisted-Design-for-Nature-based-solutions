AI-Assisted Design of Nature-Based Solutions (NbS)
A Strategic Decision-Support Framework for Integrated Flood and Pollution Management
This repository contains the agent-based simulation engine and strategic project report developed for the Fundamentals of Strategic Business Management course at the University of Genoa (Strategos) .


📌 Project Overview
Urban areas face escalating financial risks from climate-driven floods and water pollution . This project moves beyond environmental engineering to frame Nature-Based Solutions (NbS)—such as wetlands, riparian buffers, and bioswales—as a strategic investment in territorial competitiveness.

Using an Agent-Based Modeling (ABM) approach, we simulate how a city authority can allocate a €10 million budget to minimize the Cost of Inaction and maximize long-term economic resilience .
📊 Key Strategic Indicators
The simulation identifies the following economic benchmarks for a mid-sized European catchment:
Cost of Inaction (30-year NPV): €124.2 Million.
Infrastructure Restoration Multiplier: 2.5x the direct damage.
Optimal Portfolio (Strategic Wetlands): Yields an NPV of €64.7M and a 4.64:1 Benefit-Cost Ratio.
Territorial Attractiveness: Increases from a baseline of 52 to 71/100.
Technical ImplementationThe project is powered by a custom Python/Mesa calculation engine (and modeled for NetLogo integration) that evaluates thousands of spatial configurations to find the Pareto Optimal design.
Features:Strategic Utility Function: $U = (L_{avoided} + S_{long\_term}) - C_{impl}$.Stochastic Forcing: Models 1-in-10 and 1-in-50-year climate events.Economic Damage Curves: Implements depth-damage functions for residential, commercial, industrial, and infrastructure assets .
📁 Repository Structure
Report: The final strategic management report (PDF/DOCX).
code: Python scripts for the simulation engine and financial calculations.
Documentation: The complete bibliography with 40+ primary sources including ECB and World Bank data.

Academic Context
Institution: Università di Genova.
Course: Fundamentals of Strategic Business Management.
Department: Engineering Technology for Strategy and Security (Strategos).
Authors: Parag Dubey, Kanyimi Rene Uku, Ahmed Khaled Mohamed Aboshenishen .

References
The project relies on a robust evidence base including:
ECB (2025): The economic impact of floods.
Bijnens et al. (2024): Flood shocks and supply chains.
Huizinga et al. (2017): Global flood depth-damage functions.
