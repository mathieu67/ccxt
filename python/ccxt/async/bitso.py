# -*- coding: utf-8 -*-

# PLEASE DO NOT EDIT THIS FILE, IT IS GENERATED AND WILL BE OVERWRITTEN:
# https://github.com/ccxt/ccxt/blob/master/CONTRIBUTING.md#how-to-contribute-code

from ccxt.async.base.exchange import Exchange

# -----------------------------------------------------------------------------

try:
    basestring  # Python 3
except NameError:
    basestring = str  # Python 2
import json
from ccxt.base.errors import ExchangeError
from ccxt.base.errors import AuthenticationError
from ccxt.base.errors import InvalidNonce


class bitso (Exchange):

    def describe(self):
        return self.deep_extend(super(bitso, self).describe(), {
            'id': 'bitso',
            'name': 'Bitso',
            'countries': 'MX',  # Mexico
            'rateLimit': 2000,  # 30 requests per minute
            'version': 'v3',
            'has': {
                'CORS': True,
                'fetchMyTrades': True,
                'fetchOpenOrders': True,
            },
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766335-715ce7aa-5ed5-11e7-88a8-173a27bb30fe.jpg',
                'api': 'https://api.bitso.com',
                'www': 'https://bitso.com',
                'doc': 'https://bitso.com/api_info',
                'fees': 'https://bitso.com/fees?l=es',
            },
            'api': {
                'public': {
                    'get': [
                        'available_books',
                        'ticker',
                        'order_book',
                        'trades',
                    ],
                },
                'private': {
                    'get': [
                        'account_status',
                        'balance',
                        'fees',
                        'fundings',
                        'fundings/{fid}',
                        'funding_destination',
                        'kyc_documents',
                        'ledger',
                        'ledger/trades',
                        'ledger/fees',
                        'ledger/fundings',
                        'ledger/withdrawals',
                        'mx_bank_codes',
                        'open_orders',
                        'order_trades/{oid}',
                        'orders/{oid}',
                        'user_trades',
                        'user_trades/{tid}',
                        'withdrawals/',
                        'withdrawals/{wid}',
                    ],
                    'post': [
                        'bitcoin_withdrawal',
                        'debit_card_withdrawal',
                        'ether_withdrawal',
                        'orders',
                        'phone_number',
                        'phone_verification',
                        'phone_withdrawal',
                        'spei_withdrawal',
                    ],
                    'delete': [
                        'orders/{oid}',
                        'orders/all',
                    ],
                },
            },
            'exceptions': {
                '0201': AuthenticationError,  # Invalid Nonce or Invalid Credentials
                '104': InvalidNonce,  # Cannot perform request - nonce must be higher than 1520307203724237
            },
        })

    async def fetch_markets(self):
        markets = await self.publicGetAvailableBooks()
        result = []
        for i in range(0, len(markets['payload'])):
            market = markets['payload'][i]
            id = market['book']
            symbol = id.upper().replace('_', '/')
            base, quote = symbol.split('/')
            limits = {
                'amount': {
                    'min': self.safe_float(market, 'minimum_amount'),
                    'max': self.safe_float(market, 'maximum_amount'),
                },
                'price': {
                    'min': self.safe_float(market, 'minimum_price'),
                    'max': self.safe_float(market, 'maximum_price'),
                },
                'cost': {
                    'min': self.safe_float(market, 'minimum_value'),
                    'max': self.safe_float(market, 'maximum_value'),
                },
            }
            precision = {
                'amount': self.precision_from_string(market['minimum_amount']),
                'price': self.precision_from_string(market['minimum_price']),
            }
            lot = limits['amount']['min']
            result.append({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'info': market,
                'lot': lot,
                'limits': limits,
                'precision': precision,
            })
        return result

    async def fetch_balance(self, params={}):
        await self.load_markets()
        response = await self.privateGetBalance()
        balances = response['payload']['balances']
        result = {'info': response}
        for b in range(0, len(balances)):
            balance = balances[b]
            currency = balance['currency'].upper()
            account = {
                'free': float(balance['available']),
                'used': float(balance['locked']),
                'total': float(balance['total']),
            }
            result[currency] = account
        return self.parse_balance(result)

    async def fetch_order_book(self, symbol, limit=None, params={}):
        await self.load_markets()
        response = await self.publicGetOrderBook(self.extend({
            'book': self.market_id(symbol),
        }, params))
        orderbook = response['payload']
        timestamp = self.parse8601(orderbook['updated_at'])
        return self.parse_order_book(orderbook, timestamp, 'bids', 'asks', 'price', 'amount')

    async def fetch_ticker(self, symbol, params={}):
        await self.load_markets()
        response = await self.publicGetTicker(self.extend({
            'book': self.market_id(symbol),
        }, params))
        ticker = response['payload']
        timestamp = self.parse8601(ticker['created_at'])
        vwap = self.safe_float(ticker, 'vwap')
        baseVolume = self.safe_float(ticker, 'volume')
        quoteVolume = baseVolume * vwap
        last = self.safe_float(ticker, 'last')
        return {
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'high': self.safe_float(ticker, 'high'),
            'low': self.safe_float(ticker, 'low'),
            'bid': self.safe_float(ticker, 'bid'),
            'bidVolume': None,
            'ask': self.safe_float(ticker, 'ask'),
            'askVolume': None,
            'vwap': vwap,
            'open': None,
            'close': last,
            'last': last,
            'previousClose': None,
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': baseVolume,
            'quoteVolume': quoteVolume,
            'info': ticker,
        }

    def parse_trade(self, trade, market=None):
        timestamp = self.parse8601(trade['created_at'])
        symbol = None
        if market is None:
            marketId = self.safe_string(trade, 'book')
            if marketId in self.markets_by_id:
                market = self.markets_by_id[marketId]
        if market is not None:
            symbol = market['symbol']
        side = self.safe_string(trade, 'side')
        if side is None:
            side = self.safe_string(trade, 'maker_side')
        amount = self.safe_float(trade, 'amount')
        if amount is None:
            amount = self.safe_float(trade, 'major')
        if amount is not None:
            amount = abs(amount)
        fee = None
        feeCost = self.safe_float(trade, 'fees_amount')
        if feeCost is not None:
            feeCurrency = self.safe_string(trade, 'fees_currency')
            if feeCurrency is not None:
                if feeCurrency in self.currencies_by_id:
                    feeCurrency = self.currencies_by_id[feeCurrency]['code']
            fee = {
                'cost': feeCost,
                'currency': feeCurrency,
            }
        cost = self.safe_float(trade, 'minor')
        if cost is not None:
            cost = abs(cost)
        price = self.safe_float(trade, 'price')
        orderId = self.safe_string(trade, 'oid')
        return {
            'id': str(trade['tid']),
            'info': trade,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'symbol': symbol,
            'order': orderId,
            'type': None,
            'side': side,
            'price': price,
            'amount': amount,
            'cost': cost,
            'fee': fee,
        }

    async def fetch_trades(self, symbol, since=None, limit=None, params={}):
        await self.load_markets()
        market = self.market(symbol)
        response = await self.publicGetTrades(self.extend({
            'book': market['id'],
        }, params))
        return self.parse_trades(response['payload'], market, since, limit)

    async def fetch_my_trades(self, symbol=None, since=None, limit=25, params={}):
        await self.load_markets()
        market = self.market(symbol)
        # the don't support fetching trades starting from a date yet
        # use the `marker` extra param for that
        # self is not a typo, the variable name is 'marker'(don't confuse with 'market')
        markerInParams = ('marker' in list(params.keys()))
        # warn the user with an exception if the user wants to filter
        # starting from since timestamp, but does not set the trade id with an extra 'marker' param
        if (since is not None) and not markerInParams:
            raise ExchangeError(self.id + ' fetchMyTrades does not support fetching trades starting from a timestamp with the `since` argument, use the `marker` extra param to filter starting from an integer trade id')
        # convert it to an integer unconditionally
        if markerInParams:
            params = self.extend(params, {
                'marker': int(params['marker']),
            })
        request = {
            'book': market['id'],
            'limit': limit,  # default = 25, max = 100
            # 'sort': 'desc',  # default = desc
            # 'marker': id,  # integer id to start from
        }
        response = await self.privateGetUserTrades(self.extend(request, params))
        return self.parse_trades(response['payload'], market, since, limit)

    async def create_order(self, symbol, type, side, amount, price=None, params={}):
        await self.load_markets()
        order = {
            'book': self.market_id(symbol),
            'side': side,
            'type': type,
            'major': self.amount_to_precision(symbol, amount),
        }
        if type == 'limit':
            order['price'] = self.price_to_precision(symbol, price)
        response = await self.privatePostOrders(self.extend(order, params))
        return {
            'info': response,
            'id': response['payload']['oid'],
        }

    async def cancel_order(self, id, symbol=None, params={}):
        await self.load_markets()
        return await self.privateDeleteOrdersOid({'oid': id})

    def parse_order_status(self, status):
        statuses = {
            'partial-fill': 'open',  # self is a common substitution in ccxt
        }
        if status in statuses:
            return statuses['status']
        return status

    def parse_order(self, order, market=None):
        side = order['side']
        status = self.parse_order_status(order['status'])
        symbol = None
        if market is None:
            marketId = order['book']
            if marketId in self.markets_by_id:
                market = self.markets_by_id[marketId]
        if market:
            symbol = market['symbol']
        orderType = order['type']
        timestamp = self.parse8601(order['created_at'])
        amount = self.safe_float(order, 'original_amount')
        remaining = self.safe_float(order, 'unfilled_amount')
        filled = amount - remaining
        result = {
            'info': order,
            'id': order['oid'],
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'lastTradeTimestamp': None,
            'symbol': symbol,
            'type': orderType,
            'side': side,
            'price': self.safe_float(order, 'price'),
            'amount': amount,
            'cost': None,
            'remaining': remaining,
            'filled': filled,
            'status': status,
            'fee': None,
        }
        return result

    async def fetch_open_orders(self, symbol=None, since=None, limit=25, params={}):
        await self.load_markets()
        market = self.market(symbol)
        # the don't support fetching trades starting from a date yet
        # use the `marker` extra param for that
        # self is not a typo, the variable name is 'marker'(don't confuse with 'market')
        markerInParams = ('marker' in list(params.keys()))
        # warn the user with an exception if the user wants to filter
        # starting from since timestamp, but does not set the trade id with an extra 'marker' param
        if (since is not None) and not markerInParams:
            raise ExchangeError(self.id + ' fetchOpenOrders does not support fetching orders starting from a timestamp with the `since` argument, use the `marker` extra param to filter starting from an integer trade id')
        # convert it to an integer unconditionally
        if markerInParams:
            params = self.extend(params, {
                'marker': int(params['marker']),
            })
        request = {
            'book': market['id'],
            'limit': limit,  # default = 25, max = 100
            # 'sort': 'desc',  # default = desc
            # 'marker': id,  # integer id to start from
        }
        response = await self.privateGetOpenOrders(self.extend(request, params))
        orders = self.parse_orders(response['payload'], market, since, limit)
        return orders

    def sign(self, path, api='public', method='GET', params={}, headers=None, body=None):
        endpoint = '/' + self.version + '/' + self.implode_params(path, params)
        query = self.omit(params, self.extract_params(path))
        if method == 'GET':
            if query:
                endpoint += '?' + self.urlencode(query)
        url = self.urls['api'] + endpoint
        if api == 'private':
            self.check_required_credentials()
            nonce = str(self.nonce())
            request = ''.join([nonce, method, endpoint])
            if method != 'GET':
                if query:
                    body = self.json(query)
                    request += body
            signature = self.hmac(self.encode(request), self.encode(self.secret))
            auth = self.apiKey + ':' + nonce + ':' + signature
            headers = {
                'Authorization': 'Bitso ' + auth,
                'Content-Type': 'application/json',
            }
        return {'url': url, 'method': method, 'body': body, 'headers': headers}

    def handle_errors(self, httpCode, reason, url, method, headers, body):
        if not isinstance(body, basestring):
            return  # fallback to default error handler
        if len(body) < 2:
            return  # fallback to default error handler
        if (body[0] == '{') or (body[0] == '['):
            response = json.loads(body)
            if 'success' in response:
                #
                #     {"success":false,"error":{"code":104,"message":"Cannot perform request - nonce must be higher than 1520307203724237"}}
                #
                success = self.safe_value(response, 'success', False)
                if isinstance(success, basestring):
                    if (success == 'true') or (success == '1'):
                        success = True
                    else:
                        success = False
                if not success:
                    feedback = self.id + ' ' + self.json(response)
                    error = self.safe_value(response, 'error')
                    if error is None:
                        raise ExchangeError(feedback)
                    code = self.safe_string(error, 'code')
                    exceptions = self.exceptions
                    if code in exceptions:
                        raise exceptions[code](feedback)
                    else:
                        raise ExchangeError(feedback)

    async def request(self, path, api='public', method='GET', params={}, headers=None, body=None):
        response = await self.fetch2(path, api, method, params, headers, body)
        if 'success' in response:
            if response['success']:
                return response
        raise ExchangeError(self.id + ' ' + self.json(response))
