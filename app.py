from flask import Flask, render_template, request
import pickle
import numpy as np
import logging

# Load data
popular_df = pickle.load(open('C:/Users/asus/OneDrive/Desktop/new book update 1/models/popular.pkl', 'rb'))
pt = pickle.load(open('C:/Users/asus/OneDrive/Desktop/new book update 1/models/pt.pkl', 'rb'))
complete_details = pickle.load(open('C:/Users/asus/OneDrive/Desktop/new book update 1/models/complete_details.pkl', 'rb'))
similarity_scores = pickle.load(open('C:/Users/asus/OneDrive/Desktop/new book update 1/models/similarity_scores.pkl', 'rb'))
author_pt = pickle.load(open('C:/Users/asus/OneDrive/Desktop/new book update 1/models/author_pt.pkl', 'rb'))
author_similarity_scores = pickle.load(open('C:/Users/asus/OneDrive/Desktop/new book update 1/models/author_similarity_scores.pkl', 'rb'))

app = Flask(__name__, template_folder='template')

# Set up logging
logging.basicConfig(level=logging.DEBUG)

def recommend_based_author(book_author, count):
    if book_author not in author_pt.index:
        return []

    index = np.where(author_pt.index == book_author)[0][0]
    enumerated_scores = enumerate(author_similarity_scores[index])
    enumerated_list = list(enumerated_scores)
    sorted_items = sorted(enumerated_list, key=lambda x: x[1], reverse=True)
    similar_items = sorted_items[:count]

    data = []
    for i in similar_items:
        similar_author = author_pt.index[i[0]]
        temp_df = complete_details[complete_details['Book-Author'] == similar_author]

        for _, row in temp_df.drop_duplicates('Book-Title').iterrows():
            item = []
            item.append(row['Book-Title'])
            item.append(row['Book-Author'])
            item.append(row['Year-Of-Publication'])
            item.append(row['num_ratings'])
            item.append(row['avg_rating'])
            item.append(row['Image-URL-M'])
            data.append(item)

            if len(data) >= count:
                break

        if len(data) >= count:
            break

    return data

def sort_recommendations(data, sort_by):
    if sort_by == "newest":
        return sorted(data, key=lambda x: int(x[2]), reverse=True)
    elif sort_by == "oldest":
        return sorted(data, key=lambda x: int(x[2]))
    elif sort_by == "ratings":
        return sorted(data, key=lambda x: float(x[4]), reverse=True)
    return data

@app.route('/')
def recommend_d():
    return render_template('d.html')

@app.route('/home')
def index():
    return render_template('home.html',
                           book_name=list(popular_df['Book-Title'].values),
                           author=list(popular_df['Book-Author'].values),
                           image=list(popular_df['Image-URL-M'].values),
                           votes=list(popular_df['num_ratings'].values),
                           rating=list(popular_df['avg_rating'].values)
                           )

@app.route('/recommend')
def recommend_ui():
    return render_template('recommend.html')

@app.route('/about')
def about_us():
    return render_template('about.html')

@app.route('/recommend_books', methods=['post'])
def recommend():
    user_input = request.form.get('user_input')
    filter_type = request.form.get('filter_type')
    sort_by = request.form.get('sort_by')
    count = int(request.form.get('recommendation_count', 5))

    logging.debug(f"User input: {user_input}")
    logging.debug(f"Filter type: {filter_type}")
    logging.debug(f"Sort by: {sort_by}")
    logging.debug(f"Recommendation count: {count}")

    data = []
    no_recommendations = False

    if filter_type == "title":
        if user_input not in pt.index:
            logging.debug(f"Title '{user_input}' not found in pt index.")
            no_recommendations = True
        else:
            index = np.where(pt.index == user_input)[0][0]
            logging.debug(f"Index of '{user_input}' in pt: {index}")
            
            similar_items = sorted(list(enumerate(similarity_scores[index])), key=lambda x: x[1], reverse=True)[1:count+1]
            logging.debug(f"Similar items: {similar_items}")
            
            for i in similar_items:
                item = []
                temp_df = complete_details[complete_details['Book-Title'] == pt.index[i[0]]]
                logging.debug(f"Temp DataFrame for '{pt.index[i[0]]}':\n{temp_df}")

                item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Title'].values))
                item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Author'].values))
                item.extend(list(temp_df.drop_duplicates('Book-Title')['Year-Of-Publication'].values))
                item.extend(list(temp_df.drop_duplicates('Book-Title')['num_ratings'].values))
                item.extend(list(temp_df.drop_duplicates('Book-Title')['avg_rating'].values))
                item.extend(list(temp_df.drop_duplicates('Book-Title')['Image-URL-M'].values))

                data.append(item)

    elif filter_type == "author":
        data = recommend_based_author(user_input, count)
        if not data:
            no_recommendations = True

    if data:
        data = sort_recommendations(data, sort_by)

    logging.debug(f"Data: {data}")
    logging.debug(f"No recommendations: {no_recommendations}")

    return render_template('recommend.html', data=data, no_recommendations=no_recommendations, 
                           user_input=user_input, filter_type=filter_type, sort_by=sort_by, count=count)

if __name__ == '__main__':
    app.run(debug=True)
