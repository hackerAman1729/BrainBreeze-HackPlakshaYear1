from flask import Flask, render_template, request, redirect, url_for
from openai import OpenAI
import os

app = Flask(__name__)

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def get_explanation(topic, level):
    try:
        prompt_message = f"Provide an in-depth explanation suitable for a level {level} understanding on the topic: {topic}."
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt_message}
            ]
        )
        explanation = response.choices[0].message.content
        return explanation
    except Exception as e:
        return f"An error occurred while fetching the explanation: {e}"

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        topic = request.form['topic']
        return redirect(url_for('choose_level', topic=topic))
    return render_template('index.html')

@app.route('/choose_level', methods=['GET', 'POST'])
def choose_level():
    topic = request.args.get('topic') if request.method == 'GET' else request.form.get('topic')
    if request.method == 'POST':
        level = request.form.get('level')
        explanation = get_explanation(topic, level)
        return render_template('content_page.html', explanation=explanation, topic=topic)
    return render_template('choose_level.html', topic=topic)


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=80,debug=True)
