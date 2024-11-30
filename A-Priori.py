# -*- coding: utf-8 -*-
"""2.aPrioriAlgorithmFromScratch with Filter Baskets.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1db24Gm9ssn-AwDMoBRlg2Xy1YAcg4V7y
"""

import pandas as pd

dt_tag_cleaned=pd.read_csv('dt_tag_cleaned.csv')

dt_tag_cleaned.info()

dt_tag_cleaned.drop_duplicates(subset=['userId', 'movieId'], keep='last', inplace=True)
dt_tag_cleaned.info()

usersWithMovies= dt_tag_cleaned[['userId','movieId']]
usersWithMovies.info()

print('The total number of distinct movies watched by at least user',len(set(usersWithMovies['movieId'])))
print('The total number of distinct users',len(set(usersWithMovies['userId'])))

userMovies=usersWithMovies.groupby('userId')['movieId'].apply(list).reset_index(name="movieList")
userMovies

userMovies['numMoviesPerUser']  = userMovies['movieList'].str.len()
userMovies

print('On average the number of movies watched by a user is', userMovies['numMoviesPerUser'].mean())

userMovies[userMovies['numMoviesPerUser']>1000]

#users_with_plentyNumMovies=userMovies[userMovies['numMoviesPerUser']>userMovies['numMoviesPerUser'].mean()]
users_with_plentyNumMovies = userMovies[(userMovies['numMoviesPerUser'] > 2)& (userMovies['numMoviesPerUser'] < 10000) ]
users_with_plentyNumMovies

#movie_baskets=userMovies['movieList'].tolist()
movie_baskets=users_with_plentyNumMovies['movieList'].tolist()
print('The number of baskets is:',len(movie_baskets))
distinct_movies={ele for movie_basket in movie_baskets for ele in movie_basket}

import itertools
import pandas as pd

def getNumBasketsForItem(item, baskets):
    """
    Calculate the support of a single item in the baskets.
    """
    return sum(item in basket for basket in baskets) / len(baskets)

def getNumBasketsforItems(item_set, baskets):
    """
    Calculate the support of an itemset (made up of more than 1 item) in the baskets.
    """
    item_set = set(item_set)  # Convert to set once for efficiency
    return sum(item_set.issubset(basket) for basket in baskets) / len(baskets)

def aprioriFromScratch(baskets_encoded, support_threshold):
    """
    Implements the Apriori algorithm to find frequent itemsets.

    Parameters:
    - baskets_encoded: List of transactions (baskets) with encoded items.
    - support_threshold: Minimum support threshold for itemsets.

    Returns:
    - A DataFrame containing frequent itemsets and their support values.
    """
    # Initialize distinct items and calculate support for single items
    distinct_items = list({item for basket in baskets_encoded for item in basket})
    item_supports = [getNumBasketsForItem(item, baskets_encoded) for item in distinct_items]

    # Initialize result DataFrame and candidate/frequent itemsets
    result = pd.DataFrame(columns=['ItemSet', 'Support'])
    k = 1

    # Create DataFrame for single-item candidates
    candidates = pd.DataFrame({'ItemSet': [{item} for item in distinct_items], 'Support': item_supports})
    frequent_itemsets = candidates[candidates['Support'] > support_threshold].reset_index(drop=True)

    # Keep track of frequent itemsets for each iteration
    dataframes = {k: frequent_itemsets}

    # Iteratively find frequent itemsets of size k
    while not frequent_itemsets.empty:
        k += 1

        # Generate combinations of itemsets of size k
        previous_itemsets = frequent_itemsets['ItemSet'].tolist()
        candidate_itemsets = [
            set(a).union(b)  # Merge sets to generate new candidates
            for a, b in itertools.combinations(previous_itemsets, 2)
            if len(set(a).union(b)) == k
        ]

        # Deduplicate candidate itemsets
        candidate_itemsets = list({frozenset(c) for c in candidate_itemsets})

        # Calculate support for candidate itemsets
        itemset_supports = [getNumBasketsforItems(itemset, baskets_encoded) for itemset in candidate_itemsets]
        candidates = pd.DataFrame({'ItemSet': candidate_itemsets, 'Support': itemset_supports})

        # Filter itemsets with support above the threshold
        frequent_itemsets = candidates[candidates['Support'] > support_threshold]
        if not frequent_itemsets.empty:
            dataframes[k] = frequent_itemsets

    # Concatenate all frequent itemsets into the final result
    for df in dataframes.values():
        result = pd.concat([result, df], ignore_index=True)

    # Convert `frozenset` back to `set` in the final DataFrame
    result['ItemSet'] = result['ItemSet'].apply(set)
    print('Number of frequents item is ', result.shape[0])
    return result.reset_index(drop=True)

import pandas as pd


# Run Apriori algorithm implemented by Matteo
resultApriori = aprioriFromScratch(movie_baskets, support_threshold=0.03)

resultApriori

"""Check if the itemsets and their support values found by my implementation of Apriori are the same as those found using the Apriori from the mlxtend library.
Taking into account that the APriori from the mxlxtend library use itemsset as  frozenset , in the result of the Apriori implemented by hand a new column of the itemset is added and converted into frozenset.
In such way, we can compare whether the results in terms of possible frequent items found and their relative support are the same
"""

resultApriori['itemsets']=resultApriori['ItemSet']
resultApriori['itemsets']=resultApriori['itemsets'].apply(lambda x: frozenset(x))
resultApriori

from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules

te = TransactionEncoder()
te_ary = te.fit(movie_baskets).transform(movie_baskets)
df_one_hot = pd.DataFrame(te_ary, columns=te.columns_)
df_one_hot
frq_items = apriori(df_one_hot, min_support = 0.03, use_colnames = True)
frq_items

a=set(resultApriori['Support'].values)
b=set(frq_items['support'].values)
a==b

a=set(resultApriori['itemsets'].values)
b=set(frq_items['itemsets'].values)
a==b

from itertools import combinations

def generate_association_rules(resultApriori, min_confidence):
    """
    Generate association rules from a DataFrame of frequent itemsets.

    Parameters:
        frq_items (pd.DataFrame): DataFrame containing frequent itemsets and their support.
        min_confidence (float): Minimum confidence threshold for rules.

    Returns:
        List of rules with their metrics (support, confidence, lift).
    """
    rules = []

    # Map itemsets to their support for quick lookup
    support_lookup = {tuple(sorted(row['ItemSet'])): row['Support'] for _, row in resultApriori.iterrows()}

    # Iterate through each frequent itemset
    for _, row in resultApriori.iterrows():
        itemset = tuple(sorted(row['ItemSet']))
        itemset_support = row['Support']

        # Generate all possible non-empty subsets of the itemset
        subsets = [set(x) for i in range(1, len(itemset)) for x in combinations(itemset, i)]

        for subset in subsets:
            # A = subset, B = itemset - subset
            A = tuple(sorted(subset))
            B = tuple(sorted(set(itemset) - subset))

            # Calculate metrics
            A_support = support_lookup.get(A, 0)
            B_support = support_lookup.get(B, 0)

            if A_support > 0:  # Avoid division by zero
                confidence = itemset_support / A_support
                lift = confidence / B_support if B_support > 0 else 0

                # Add rule if it meets the confidence threshold
                if confidence >= min_confidence:
                    rules.append({
                        'antecedent': A,
                        'consequent': B,
                        'support': itemset_support,
                        'confidence': confidence,
                        'lift': lift
                    })
    print('The number of rules is' ,len(rules))

    for rule in rules:
      print(f"Rule: {rule['antecedent']} => {rule['consequent']}, "
          f"Support: {rule['support']:.2f}, Confidence: {rule['confidence']:.2f}, Lift: {rule['lift']:.2f}")

    return pd.DataFrame(rules)
# Generate rules
rules = generate_association_rules(resultApriori, min_confidence=0.5)


rules

"""We are attempting to generate new rules by modifying the minimum support in the Apriori algorithm as well as adjusting the confidence threshold.



"""
print('By running Apriori  with support_threshold=0.025 and association rules with  min_confidence=0.5 we get')
resultApriori = aprioriFromScratch(movie_baskets, support_threshold=0.025)
resultApriori

rules = generate_association_rules(resultApriori, min_confidence=0.5)
rules

print('By running Apriori  with support_threshold=0.025 and association rules with  min_confidence=0.7 we get')
rules = generate_association_rules(resultApriori, min_confidence=0.7)
rules

resultApriori = aprioriFromScratch(movie_baskets, support_threshold=0.018)
resultApriori
print('By running Apriori  with support_threshold=0.018 and association rules with  min_confidence=0.7 we get')
rules = generate_association_rules(resultApriori, min_confidence=0.7)
rules
print('By running Apriori  with support_threshold=0.018 and association rules with  min_confidence=0.8 we get')
rules = generate_association_rules(resultApriori, min_confidence=0.8)
rules

resultApriori = aprioriFromScratch(movie_baskets, support_threshold=0.008)
resultApriori
print('By running Apriori  with support_threshold=0.008 and association rules with  min_confidence=0.8 we get')

rules = generate_association_rules(resultApriori, min_confidence=0.8)
rules
print('By running Apriori  with support_threshold=0.008 and association rules with  min_confidence=0.9 we get')

rules = generate_association_rules(resultApriori, min_confidence=0.9)
rules
print('By running Apriori  with support_threshold=0.008 and association rules with  min_confidence=0.95 we get')

rules = generate_association_rules(resultApriori, min_confidence=0.95)
rules
print('By running Apriori  with support_threshold=0.008 and association rules with  min_confidence=0.98 we get')

rules = generate_association_rules(resultApriori, min_confidence=0.98)
rules