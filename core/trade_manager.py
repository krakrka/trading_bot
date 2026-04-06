# core/trade_manager.py

def get_precision(price: float) -> int:
    """Détermine le nombre de décimales nécessaires selon le prix."""
    if price >= 1000: return 2      # BTC, ETH, Gold, NASDAQ
    if price >= 1: return 4         # SOL, LINK, AVAX
    return 6                        # ADA, et autres petites cryptos

def calculate_position(current_price: float, atr: float, prediction: int):
    """
    Calcule le plan de trade avec une précision adaptée à l'actif.
    """
    precision = get_precision(current_price)
    
    if prediction == 1:
        direction = "ACHAT"
        stop_loss = current_price - (1.5 * atr)
        take_profit = current_price + (3.0 * atr)
    else:
        direction = "VENTE"
        stop_loss = current_price + (1.5 * atr)
        take_profit = current_price - (3.0 * atr)
        
    return {
        "direction": direction,
        "entry_price": round(current_price, precision),
        "stop_loss": round(stop_loss, precision),
        "take_profit": round(take_profit, precision)
    }