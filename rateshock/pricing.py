"""Bond pricing and duration functions."""


def bond_price(face, coupon_rate, years, market_rate):
    """Price of a bond paying an annual coupon, discounted at market_rate."""
    price = 0
    for t in range(1, years + 1):
        cash = face * coupon_rate
        if t == years:
            cash += face
        price += cash / (1 + market_rate) ** t
    return price


def duration(face, coupon_rate, years, market_rate, bump=0.0001):
    """Approximate % price change for a 1% (100 bps) move in rates."""
    p = bond_price(face, coupon_rate, years, market_rate)
    p_down = bond_price(face, coupon_rate, years, market_rate - bump)
    p_up = bond_price(face, coupon_rate, years, market_rate + bump)
    return (p_down - p_up) / (2 * p * bump)


def bucket_duration(maturity, rate=0.07):
    """Duration for a maturity bucket, assuming a par bond at `rate`."""
    if maturity < 1:
        return maturity
    return duration(100, rate, int(round(maturity)), rate)
