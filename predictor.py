import numpy as np
from collections import deque
from dataclasses import dataclass, field
from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)

@dataclass
class GameResult:
    """Structured representation of a past mine game."""
    multiplier: float
    profit: float
    mines_count: int
    tiles_revealed: int
    timestamp: float

class CustomStatisticalAlgo:
    """
    Custom algorithm based on Volatility Clustering and Kelly Criterion.
    NOTE: This analyzes RISK, not mine locations. Mines are provably fair RNG.
    """
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.history: deque[GameResult] = deque(maxlen=window_size)
        self.consecutive_losses = 0
        self.session_pnl = 0.0
        
    def add_result(self, result: GameResult):
        self.history.append(result)
        self.session_pnl += result.profit
        if result.profit < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
            
    def get_volatility_score(self) -> float:
        """Returns 0-1 score indicating current risk level."""
        if len(self.history) < 20:
            return 0.5  # Neutral until enough data
            
        profits = [g.profit for g in self.history]
        std_dev = np.std(profits)
        mean_profit = np.mean(profits)
        
        # High volatility + negative mean = DANGER
        if std_dev == 0:
            return 0.5
            
        risk_score = max(0, min(1, (std_dev / (abs(mean_profit) + 1)) * 0.3))
        return risk_score
    
    def should_play(self, base_bet: float, balance: float) -> Dict:
        """
        Returns recommendation based on custom algo analysis.
        """
        volatility = self.get_volatility_score()
        
        # Dynamic bet sizing based on Kelly-inspired risk management
        if self.consecutive_losses > 5:
            action = "PAUSE"
            reason = f"Cold streak detected ({self.consecutive_losses} losses). Cooling off."
            bet_size = 0
        elif volatility > 0.7:
            action = "REDUCE"
            reason = f"High volatility ({volatility:.2f}). Reducing exposure."
            bet_size = base_bet * 0.5
        elif self.session_pnl < -(balance * 0.1):
            action = "STOP"
            reason = "Session loss limit reached (-10%)."
            bet_size = 0
        else:
            action = "PLAY"
            reason = f"Conditions normal. Volatility: {volatility:.2f}"
            bet_size = base_bet
            
        return {
            "action": action,
            "bet_size": round(bet_size, 4),
            "reason": reason,
            "volatility": round(volatility, 4),
            "consecutive_losses": self.consecutive_losses,
            "session_pnl": round(self.session_pnl, 4)
        }


class BloxflipPredictor:
    """Main predictor class - FIXED: Class defined before instantiation."""
    
    def __init__(self):
        self.algo = CustomStatisticalAlgo(window_size=200)
        self.auth_token: Optional[str] = None
        logger.info("BloxflipPredictor initialized with Custom Statistical Algo")
        
    def analyze_history(self, games: List[Dict]) -> Dict:
        """Process raw API history into algo-friendly format."""
        for game in games:
            try:
                result = GameResult(
                    multiplier=float(game.get('multiplier', 0)),
                    profit=float(game.get('profit', 0)),
                    mines_count=int(game.get('mines', 3)),
                    tiles_revealed=int(game.get('tilesRevealed', 0)),
                    timestamp=float(game.get('createdAt', 0))
                )
                self.algo.add_result(result)
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping malformed game record: {e}")
                
        return self.algo.should_play(
            base_bet=self._get_base_bet(),
            balance=self._get_balance()
        )
    
    def _get_base_bet(self) -> float:
        """Override or configure externally."""
        return getattr(self, 'base_bet', 10.0)
    
    def _get_balance(self) -> float:
        """Override or configure externally."""
        return getattr(self, 'balance', 1000.0)


class BloxflipAuth:
    """Handles authentication separately from prediction logic."""
    
    def __init__(self, token: str = ""):
        self.token = token
        
    def is_valid(self) -> bool:
        return bool(self.token and len(self.token) > 10)


# ✅ SAFE INSTANTIATION - Class is fully defined above this line
predictor = BloxflipPredictor()
