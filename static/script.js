let gameId = null;
let difficulty = null;
let isGameOver = false;
let timerInterval = null;
let seconds = 0;
let firstGameMove = true;
let isMusicStarted = false;
let bgMusic = null;

window.lastConfidence = null;

document.addEventListener("DOMContentLoaded", () => {
     const mainContainer = document.querySelector(".difficulty-options");
     if (mainContainer) {
          const cards = document.querySelectorAll(".difficulty-card");
          function updateSelectedCard() {
               cards.forEach((c) =>
                    c.classList.toggle(
                         "selected",
                         c.querySelector("input").checked
                    )
               );
          }
          cards.forEach((c) =>
               c.addEventListener("click", () => {
                    c.querySelector("input").checked = true;
                    updateSelectedCard();
               })
          );
          updateSelectedCard();
     }

     const gameContainer = document.querySelector(".content-wrapper.game-page");
     if (gameContainer) {
          gameId = parseInt(gameContainer.dataset.gameId, 10);
          difficulty = gameContainer.dataset.difficulty;
          bgMusic = document.getElementById("background-music");
          initializeGame();

          // Immediately show initial confidence grid on load if checked
          if (document.getElementById("show-confidence")?.checked && window.initialConfidence) {
          const dummyBoard = Array.from({ length: window.initialConfidence.length }, () =>
               Array(window.initialConfidence[0].length).fill("hidden")
          );
          updateBoard(dummyBoard, window.initialConfidence);
          }


          const muteBtn = document.getElementById("mute-btn");
          if (bgMusic && muteBtn) {
               bgMusic.volume = 0.1;
               muteBtn.addEventListener("click", () => {
                    if (bgMusic.paused) {
                         if (isMusicStarted) {
                              bgMusic.play();
                         }
                         muteBtn.textContent = "🔊";
                    } else {
                         bgMusic.pause();
                         muteBtn.textContent = "🔇";
                    }
               });
          }

          const confidenceCheckbox = document.getElementById("show-confidence");
          confidenceCheckbox.addEventListener("change", () => {
               confidenceCheckbox.addEventListener("change", () => {
               if (confidenceCheckbox.checked) {
                    if (firstGameMove && window.initialConfidence) {
                         const dummyBoard = Array.from({ length: window.initialConfidence.length }, () =>
                              Array(window.initialConfidence[0].length).fill("hidden")
                         );
                         updateBoard(dummyBoard, window.initialConfidence);
                    } else {
                         makeMove(-1, -1, "getInfo");
                    }
               } else {
                    document.querySelectorAll(".confidence-text").forEach((el) => (el.style.display = "none"));
                    document.querySelectorAll(".tile").forEach((tile) => tile.classList.remove("high-risk"));
               }
               });

          });

          document.getElementById("play-again-btn").addEventListener("click", () => (window.location.href = "/"));
     }
});

function initializeGame() {
     renderGameBoard(difficulty);
     updateGameInfo({ human: 0, ai: 0 }, getMineCount(difficulty), { human: 0, ai: 0 });
     startTimer();
     if (document.getElementById("show-confidence")?.checked && window.initialConfidence) {
    updateBoard(Array.from({ length: window.initialConfidence.length }, () =>
        Array(window.initialConfidence[0].length).fill("hidden")
    ), window.initialConfidence);
}

}

function startTimer() {
     if (timerInterval) clearInterval(timerInterval);
     seconds = 0;
     const timerEl = document.getElementById("timer");
     timerEl.textContent = "00:00";
     timerInterval = setInterval(() => {
          seconds++;
          const mins = Math.floor(seconds / 60).toString().padStart(2, "0");
          const secs = (seconds % 60).toString().padStart(2, "0");
          timerEl.textContent = `${mins}:${secs}`;
     }, 1000);
}

function stopTimer() {
     if (timerInterval) clearInterval(timerInterval);
}

function renderGameBoard(diff) {
     const container = document.getElementById("game-container");
     container.innerHTML = "";
     let width, height;
     switch (diff) {
          case "easy": width = 9; height = 9; break;
          case "medium": width = 16; height = 16; break;
          case "hard": width = 30; height = 16; break;
     }
     container.style.gridTemplateColumns = `repeat(${width}, 40px)`;
     for (let y = 0; y < height; y++) {
          for (let x = 0; x < width; x++) {
               const tile = document.createElement("div");
               tile.className = "tile hidden";
               tile.dataset.x = x;
               tile.dataset.y = y;
               tile.addEventListener("click", () => handleTileClick(tile, x, y));
               tile.addEventListener("contextmenu", (e) => {
                    e.preventDefault();
                    handleRightClick(tile, x, y);
               });
               container.appendChild(tile);
          }
     }
}

function primeAudio() {
     if (firstGameMove) {
          const lossSound = document.getElementById("loss-sound");
          const winSound = document.getElementById("win-sound");
          if (lossSound) { lossSound.play().catch(() => {}); lossSound.pause(); }
          if (winSound) { winSound.play().catch(() => {}); winSound.pause(); }
          if (bgMusic) { bgMusic.play().catch(() => {}); bgMusic.pause(); }
          firstGameMove = false;
     }
}

function handleTileClick(tileElement, x, y) {
     primeAudio();
     if (isGameOver || !tileElement.classList.contains("hidden")) return;
     tileElement.classList.add("player-move");
     makeMove(x, y, "reveal");
}

function handleRightClick(tileElement, x, y) {
     primeAudio();
     if (isGameOver || !tileElement.classList.contains("hidden")) return;
     tileElement.classList.add("player-move");
     makeMove(x, y, "flag");
}

function makeMove(x, y, action) {
     if (action !== "getInfo" && isGameOver) return;
     if (!isMusicStarted && bgMusic) {
          bgMusic.play().catch(e => console.error("Autoplay was prevented:", e));
          isMusicStarted = true;
     }

     const showConfidence = document.getElementById("show-confidence").checked;

     fetch("/move", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ game_id: gameId, x, y, action, show_confidence: showConfidence })
     })
     .then(res => res.json())
     .then(data => {
          if (data.error) return console.error(data.error);

          let confidence = data.ai_confidence;

          if (!confidence && window.lastConfidence && document.getElementById("show-confidence").checked) {
          confidence = window.lastConfidence;
          }

          if (data.ai_confidence) {
    window.lastConfidence = data.ai_confidence;
}
     const confidenceToShow = document.getElementById("show-confidence").checked ? window.lastConfidence : null;
     updateBoard(data.player_board, confidenceToShow);


          if (confidence) {
          window.lastConfidence = confidence; // save for fallback on next move
          }

          if (action === "getInfo") return;

          const oldScores = {
               human: parseInt(document.getElementById("human-score").textContent, 10),
               ai: parseInt(document.getElementById("ai-score").textContent, 10)
          };
          updateGameInfo(data.scores, data.mines_left, oldScores);

          if (data.points_gained) {
               showPointsGained(x, y, data.points_gained.human, 'human');
               if (data.ai_move) {
                    showPointsGained(data.ai_move.x, data.ai_move.y, data.points_gained.ai, 'ai');
               }
          }

          const aiStatusEl = document.getElementById("ai-status");
          if (data.ai_move) {
               const { action: aiAction, x: aiX, y: aiY } = data.ai_move;
               aiStatusEl.textContent = `AI's move: ${aiAction.charAt(0).toUpperCase() + aiAction.slice(1)}ed tile (${aiX}, ${aiY})`;
               const aiTile = document.querySelector(`.tile[data-x="${aiX}"][data-y="${aiY}"]`);
               if (aiTile) aiTile.classList.add("ai-move");
          } else if (!data.game_over) {
               aiStatusEl.textContent = "It's your turn.";
          } else {
               aiStatusEl.textContent = "Game Over!";
          }

          if (data.game_over) {
               isGameOver = true;
               stopTimer();
               showGameOverModal(data.winner, data.scores);
          }
     })
     .catch(err => console.error("Error:", err));
}

function showPointsGained(x, y, points, player) {
     if (points === 0) return;
     const tile = document.querySelector(`.tile[data-x="${x}"][data-y="${y}"]`);
     if (!tile) return;
     const el = document.createElement("div");
     el.className = `points-gained ${player}-points`;
     el.textContent = (points > 0 ? '+' : '') + points.toFixed(1);
     tile.appendChild(el);
     setTimeout(() => el.remove(), 1000);
}

function updateBoard(board, aiConfidence) {
    const showConfidence = document.getElementById("show-confidence").checked;
    let maxConfidence = -1;
    let minConfidence = 1;
    let maxConfidenceTiles = [];

    if (aiConfidence) {
        for (let y = 0; y < aiConfidence.length; y++) {
            for (let x = 0; x < aiConfidence[y].length; x++) {
                const conf = aiConfidence[y][x];
                if (typeof conf === "number" && conf >= 0) {
                    if (conf > maxConfidence) {
                        maxConfidence = conf;
                        maxConfidenceTiles = [{ x, y }];
                    } else if (conf === maxConfidence) {
                        maxConfidenceTiles.push({ x, y });
                    }
                    if (conf < minConfidence) {
                        minConfidence = conf;
                    }
                }
            }
        }
    }

    const highlightRisk = maxConfidence !== minConfidence;

    board.forEach((row, y) => {
        row.forEach((cell, x) => {
            const tile = document.querySelector(`.tile[data-x="${x}"][data-y="${y}"]`);
            if (!tile) return;

            const prev = tile.className;
            tile.className = "tile";
            tile.innerHTML = "";
            const img = document.createElement("img");
            img.className = "tile-icon";

            if (cell === "hidden") {
                tile.classList.add("hidden");
                if (aiConfidence && typeof aiConfidence[y][x] === "number" && aiConfidence[y][x] >= 0) {
                    const confValue = aiConfidence[y][x];
                    const confidenceText = document.createElement("span");
                    confidenceText.className = "confidence-text";
                    confidenceText.textContent = `${Math.round(confValue * 1000) / 10}%`;
                    console.log(`Confidence @ (${x}, ${y}): ${aiConfidence[y][x]}`);
                    confidenceText.style.display = showConfidence ? "block" : "none";
                    tile.appendChild(confidenceText);
                    if (showConfidence && highlightRisk && confValue === maxConfidence) {
                        tile.classList.add("high-risk");
                    }
                }
            } else if (cell === "flagged") {
                tile.classList.add("flagged");
                img.src = "/static/icons/flag.png";
                tile.appendChild(img);
            } else if (cell === "mine") {
                tile.classList.add("mine");
                img.src = "/static/icons/dog.png";
                tile.appendChild(img);
                if (prev.includes("hidden")) tile.classList.add("mine-hit");
            } else if (cell === "wrong_flag") {
                tile.classList.add("wrong-flag");
                tile.textContent = "💔";
            } else {
                tile.classList.add("revealed");
                if (typeof cell === "number" && cell > 0) {
                    tile.textContent = cell;
                    tile.classList.add(`tile-${cell}`);
                }
            }
        });
    });
}

function updateGameInfo(newScores, minesLeft, oldScores) {
     const humanScoreEl = document.getElementById("human-score");
     const aiScoreEl = document.getElementById("ai-score");
     if (newScores.human !== oldScores.human) {
          humanScoreEl.classList.add("score-updated");
          setTimeout(() => humanScoreEl.classList.remove("score-updated"), 500);
     }
     if (newScores.ai !== oldScores.ai) {
          aiScoreEl.classList.add("score-updated");
          setTimeout(() => aiScoreEl.classList.remove("score-updated"), 500);
     }
     humanScoreEl.textContent = newScores.human;
     aiScoreEl.textContent = newScores.ai;
     document.getElementById("mines-left").textContent = minesLeft;
}

function showGameOverModal(winner, scores) {
     const modal = document.getElementById("game-over-modal");
     const winnerText = document.getElementById("modal-winner-text");
     const subtitleText = document.getElementById("modal-subtitle");
     const finalScoreText = document.getElementById("modal-final-score");
     const lossSound = document.getElementById("loss-sound");
     const winSound = document.getElementById("win-sound");

     if (bgMusic) bgMusic.pause();

     if (winner === "human") {
          winnerText.textContent = "🎉 You Win! 🎉";
          subtitleText.textContent = "You are the top cat!";
          if (winSound) winSound.play();
     } else if (winner === "ai") {
          winnerText.textContent = "🤖 AI Wins...";
          subtitleText.textContent = "Don't worry, you'll get 'em next time!";
          if (lossSound) lossSound.play();
     } else {
          winnerText.textContent = "😐 It's a Tie! 😐";
          subtitleText.textContent = "A purrfectly balanced match!";
     }
     finalScoreText.textContent = `Final Score: Human ${scores.human} - AI ${scores.ai}`;
     modal.classList.remove("hidden");
}

const gameOverModal = document.getElementById("game-over-modal");
const closeModalBtn = document.getElementById("close-modal-btn");
closeModalBtn.addEventListener("click", () => gameOverModal.classList.add("hidden"));
gameOverModal.addEventListener("click", (e) => {
     if (e.target === gameOverModal) gameOverModal.classList.add("hidden");
});

function getMineCount(diff) {
     switch (diff) {
          case "easy": return 10;
          case "medium": return 40;
          case "hard": return 99;
          default: return 0;
     }
}