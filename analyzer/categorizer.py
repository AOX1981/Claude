import re

# Category definitions with keywords
NECESSARY_CATEGORIES = {
    'groceries': [
        'grocery', 'supermarket', 'market', 'walmart', 'target', 'costco',
        'whole foods', 'trader joe', 'safeway', 'kroger', 'publix', 'aldi',
        'food lion', 'wegmans', 'heb', 'albertsons', 'food market'
    ],
    'utilities': [
        'electric', 'power', 'water', 'gas', 'utility', 'energy',
        'internet', 'cable', 'phone', 'mobile', 'wireless', 'verizon',
        'at&t', 'comcast', 'spectrum', 'xfinity'
    ],
    'housing': [
        'rent', 'mortgage', 'landlord', 'property management', 'lease',
        'housing', 'apartment', 'hoa'
    ],
    'healthcare': [
        'pharmacy', 'cvs', 'walgreens', 'rite aid', 'medical', 'doctor',
        'hospital', 'clinic', 'health', 'prescription', 'dental', 'vision',
        'insurance health', 'copay', 'lab corp'
    ],
    'transportation': [
        'gas station', 'fuel', 'shell', 'chevron', 'exxon', 'bp', 'mobil',
        'car payment', 'auto loan', 'car insurance', 'parking', 'toll',
        'public transit', 'metro', 'bus fare', 'train'
    ],
    'insurance': [
        'insurance', 'life insurance', 'auto insurance', 'home insurance',
        'renters insurance'
    ],
    'education': [
        'tuition', 'school', 'university', 'college', 'student loan',
        'textbook', 'course', 'education'
    ]
}

FRIVOLOUS_CATEGORIES = {
    'dining_out': [
        'restaurant', 'cafe', 'coffee', 'starbucks', 'dunkin', 'mcdonald',
        'burger', 'pizza', 'taco', 'chipotle', 'panera', 'subway',
        'wendys', 'chick-fil-a', 'dominos', 'kfc', 'dining', 'bar',
        'pub', 'grill', 'bistro', 'diner', 'eatery', 'food delivery',
        'doordash', 'uber eats', 'grubhub', 'postmates'
    ],
    'entertainment': [
        'netflix', 'hulu', 'disney', 'spotify', 'apple music', 'youtube',
        'amazon prime video', 'hbo', 'movie', 'cinema', 'theater',
        'concert', 'ticket', 'event', 'game', 'gaming', 'steam',
        'playstation', 'xbox', 'nintendo'
    ],
    'shopping': [
        'amazon', 'ebay', 'etsy', 'mall', 'clothing', 'fashion',
        'boutique', 'nike', 'adidas', 'gap', 'old navy', 'macys',
        'nordstrom', 'sephora', 'ulta', 'best buy', 'electronics',
        'jewelry', 'accessories'
    ],
    'luxury': [
        'spa', 'salon', 'massage', 'manicure', 'pedicure', 'hair',
        'luxury', 'premium', 'fine dining', 'country club', 'golf'
    ],
    'alcohol_tobacco': [
        'liquor', 'wine', 'beer', 'bar', 'brewery', 'distillery',
        'tobacco', 'vape', 'cigar'
    ],
    'subscriptions': [
        'subscription', 'membership', 'monthly fee', 'annual fee',
        'gym', 'fitness', 'planet fitness', '24 hour fitness'
    ],
    'impulse': [
        'convenience store', '7-eleven', 'circle k', 'wawa',
        'snack', 'candy', 'soda', 'energy drink'
    ]
}

def categorize_transactions(transactions):
    """
    Categorize transactions into frivolous and necessary expenses.

    Args:
        transactions: List of transaction dictionaries

    Returns:
        Dictionary with 'frivolous' and 'necessary' lists
    """
    frivolous = []
    necessary = []

    for transaction in transactions:
        # Only categorize debit transactions (expenses)
        if transaction['type'] != 'debit':
            continue

        description = transaction['description'].lower()
        category, category_name = determine_category(description)

        # Add category information to transaction
        transaction_with_category = transaction.copy()
        transaction_with_category['category'] = category_name

        if category == 'frivolous':
            frivolous.append(transaction_with_category)
        elif category == 'necessary':
            necessary.append(transaction_with_category)
        else:
            # If uncertain, categorize as frivolous to be conservative
            # User can review and adjust
            transaction_with_category['category'] = 'unclassified (marked as frivolous)'
            frivolous.append(transaction_with_category)

    return {
        'frivolous': frivolous,
        'necessary': necessary
    }

def determine_category(description):
    """
    Determine if a transaction is frivolous or necessary based on description.

    Returns:
        Tuple of (category_type, specific_category_name)
        where category_type is 'frivolous' or 'necessary'
    """
    # Check necessary categories first
    for category_name, keywords in NECESSARY_CATEGORIES.items():
        for keyword in keywords:
            if keyword in description:
                return ('necessary', category_name)

    # Check frivolous categories
    for category_name, keywords in FRIVOLOUS_CATEGORIES.items():
        for keyword in keywords:
            if keyword in description:
                return ('frivolous', category_name)

    # Default: uncertain (will be marked as frivolous)
    return ('uncertain', 'unclassified')

def calculate_totals(categorized_transactions):
    """
    Calculate total amounts for all categories.

    Args:
        categorized_transactions: Dictionary with 'frivolous' and 'necessary' lists

    Returns:
        Dictionary with total amounts
    """
    frivolous_total = sum(t['amount'] for t in categorized_transactions['frivolous'])
    necessary_total = sum(t['amount'] for t in categorized_transactions['necessary'])
    total_expenses = frivolous_total + necessary_total

    # Calculate category breakdowns
    frivolous_by_category = {}
    for transaction in categorized_transactions['frivolous']:
        category = transaction['category']
        if category not in frivolous_by_category:
            frivolous_by_category[category] = 0
        frivolous_by_category[category] += transaction['amount']

    necessary_by_category = {}
    for transaction in categorized_transactions['necessary']:
        category = transaction['category']
        if category not in necessary_by_category:
            necessary_by_category[category] = 0
        necessary_by_category[category] += transaction['amount']

    return {
        'total_expenses': round(total_expenses, 2),
        'frivolous_total': round(frivolous_total, 2),
        'necessary_total': round(necessary_total, 2),
        'frivolous_percentage': round((frivolous_total / total_expenses * 100) if total_expenses > 0 else 0, 2),
        'frivolous_by_category': {k: round(v, 2) for k, v in frivolous_by_category.items()},
        'necessary_by_category': {k: round(v, 2) for k, v in necessary_by_category.items()},
        'transaction_count': len(categorized_transactions['frivolous']) + len(categorized_transactions['necessary'])
    }
