INSERT INTO symbol_registry(symbol_canonique, base, quote, aliases) VALUES
('BTC-USDT','BTC','USDT','{"binance":"BTCUSDT","coinbase":null}'),
('ETH-USDT','ETH','USDT','{"binance":"ETHUSDT","coinbase":null}'),
('SOL-USDT','SOL','USDT','{"binance":"SOLUSDT","coinbase":null}'),
('XRP-USDT','XRP','USDT','{"binance":"XRPUSDT","coinbase":null}'),
('ADA-USDT','ADA','USDT','{"binance":"ADAUSDT","coinbase":null}'),
('DOGE-USDT','DOGE','USDT','{"binance":"DOGEUSDT","coinbase":null}'),
('AVAX-USDT','AVAX','USDT','{"binance":"AVAXUSDT","coinbase":null}'),
('LINK-USDT','LINK','USDT','{"binance":"LINKUSDT","coinbase":null}'),
('MATIC-USDT','MATIC','USDT','{"binance":"MATICUSDT","coinbase":null}'),
('LTC-USDT','LTC','USDT','{"binance":"LTCUSDT","coinbase":null}'),

('BTC-USD','BTC','USD','{"binance":null,"coinbase":"BTC-USD"}'),
('ETH-USD','ETH','USD','{"binance":null,"coinbase":"ETH-USD"}'),
('SOL-USD','SOL','USD','{"binance":null,"coinbase":"SOL-USD"}'),
('XRP-USD','XRP','USD','{"binance":null,"coinbase":"XRP-USD"}'),
('ADA-USD','ADA','USD','{"binance":null,"coinbase":"ADA-USD"}'),
('DOGE-USD','DOGE','USD','{"binance":null,"coinbase":"DOGE-USD"}'),
('AVAX-USD','AVAX','USD','{"binance":null,"coinbase":"AVAX-USD"}'),
('LINK-USD','LINK','USD','{"binance":null,"coinbase":"LINK-USD"}'),
('MATIC-USD','MATIC','USD','{"binance":null,"coinbase":"MATIC-USD"}'),
('LTC-USD','LTC','USD','{"binance":null,"coinbase":"LTC-USD"}')
ON CONFLICT (symbol_canonique) DO NOTHING;
 