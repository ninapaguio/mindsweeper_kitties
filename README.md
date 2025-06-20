# 🧠 MindSweeper

**MindSweeper** is a competitive, AI-powered twist on the classic Minesweeper game. In this version, players race against an intelligent computer opponent to uncover hidden "dogs" on a grid by revealing or flagging tiles. Built with logic-based mechanics and probabilistic decision-making, MindSweeper is not just about luck — it's about strategy, reasoning, and smart plays.

---

## 🎮 Game Overview

- **Genre:** Puzzle / Strategy  
- **Players:** Single Player vs AI  
- **Goal:** Outscore the AI by revealing safe tiles and correctly flagging dogs (bombs).  
- **Unique Feature:** Real-time competition against a belief-state AI that adapts to revealed clues.

---

## 🧩 Key Features

- 🤖 **Belief-State AI:** Uses probability and logic to make smart decisions under uncertainty.
- 📈 **Confidence Meter:** Tiles reflect the probability of hiding a dog based on surrounding clues.
- 🎯 **Score Buffs:** Flag special dog tiles and earn a +20% score boost for comeback potential.
- ⚔️ **Competitive Gameplay:** Shared tiles and tie-breakers increase intensity and depth.

---

## ⚙️ Game Mechanics

### 📊 Difficulty Levels
- **Easy:** 9×9 grid with 10 dogs  
- **Medium:** 16×16 grid with 40 dogs  
- **Hard:** 30×16 grid with 99 dogs  

### 🔁 Turn-Based Play
- Both the player and AI choose a tile each turn to reveal or flag.
- Tiles may reveal:
  - A number (indicating nearby dogs)
  - A blank (0)
  - A dog (penalty)

### 🧠 Confidence Logic
- Each tile has a confidence score estimating dog probability.
- Logic:
  - **100% chance:** Flag
  - **0% chance:** Reveal
  - **Otherwise:** Choose tile with the lowest risk

### 🏅 Scoring System
| Action                       | Points   |
|-----------------------------|----------|
| Flagged correct dog         | +10      |
| Incorrect flag              | -4       |
| Revealed numbered tile      | +2       |
| Revealed blank tile (0)     | 0        |
| Revealed dog (mistake)      | -20      |
| Same tile picked by both    | Shared   |

### 🚨 End Conditions
- All dogs are correctly flagged  
- A player reaches the target score  
- A player reveals too many dogs (automatic loss)

---

## 🤖 AI Implementation

MindSweeper’s AI is powered by a **Belief-State Search Algorithm**, ideal for environments with incomplete information. The AI:
- Maintains a probability map of the grid (belief states)
- Updates confidence levels each round as new information is revealed
- Selects the best move based on risk-reward logic

This enables the AI to simulate human-like reasoning and provide a challenging gameplay experience.

---

## 🏗️ Architecture Overview

- **Game Engine**: Manages rounds, player actions, and state updates
- **Grid Manager**: Handles tile logic and score computation
- **AI Module**:
  - **Belief State Manager**: Updates probabilities
  - **Decision Engine**: Chooses optimal move
- **UI Module**: Displays board and results to the player

---

## 🚀 Getting Started

1. In terminal
   > pip install flask
2. To run the program
   > python app.py
