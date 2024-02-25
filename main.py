from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
import os
import warnings
import requests
from openai import OpenAI
from exa_py import Exa

app = Flask(__name__)

warnings.filterwarnings("ignore", category=DeprecationWarning)


client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
exa_client = Exa(api_key=os.getenv('EXA_API_KEY'))


def generate_random_topic():
  response = client.chat.completions.create(
      model="gpt-3.5-turbo",
      messages=[{
          "role": "system",
          "content": "You are a knowledgeable assistant."
      }, {
          "role":
          "user",
          "content":
          "Suggest a random interesting topic. random topic like from rocket propulsion, to nylon thread, to history topic, to some historic sport event, to radio technology, to harmoic motion to lithium mining to essential proteins etc etc. The topics should not be limited to that as I just mentioned them as an example like how niche the topics can be, and the topics can be technical,scientific, financial,literary,historic world leaders also. The most likely topics are already done so go niche. Just give the topic and say nothing else. "
      }])
  topic = response.choices[0].message.content.strip()
  return topic


def get_resources(topic):
  try:
    results = exa_client.search_and_contents(topic,
                                             use_autoprompt=True,
                                             num_results=1,
                                             text=True)
    if results.results and len(results.results) > 0:
      content = results.results[0].text  # Text content
      url = results.results[0].url  # URL of the source
      return content, url
    else:
      return "No content found for the given topic.", ""
  except Exception as e:
    print(f"Error fetching resources from Exa: {e}")
    return "An error occurred while fetching resources.", ""


def get_video_resource(topic):
  try:
    results = exa_client.search(
        topic,
        num_results=1,
        include_domains=["youtube.com"],
        use_autoprompt=True,
    )

    # print(results)
    if results.results and len(results.results) > 0:
      video_url = results.results[0].url
      return video_url
    else:
      return ""
  except Exception as e:
    print(f"Error fetching video resources from Exa: {e}")
    return ""


def summarize_content(content):
  response = client.chat.completions.create(
      model="gpt-3.5-turbo",
      messages=[{
          "role": "system",
          "content": "You are a concise assistant."
      }, {
          "role":
          "user",
          "content":
          f"Summarize this in 100 words, make sure that you keep it concise yet interesting, factfully correct,  And if there are some articles so don't say things like in this article the writer is saying this and that . just talk about what is being said, the main theme.: {content}"
      }])
  summary = response.choices[0].message.content.strip()
  return summary


@app.route('/')
def home():
  return render_template('index.html')

# ---  calling dalle for images ---
# def get_topic_image(topic):
#   try:
#       response = client.images.generate(
#           model="dall-e-2",
#           prompt=topic,
#           n=1,
#           size="1024x1024"  
#       )
#       image_url = response.data[0].url

#       return image_url
#   except Exception as e:
#       print(f"Error fetching image for topic: {e}")
#       return ""


#calling unspash for images
def get_topic_image(topic):
    access_key = os.getenv('UNSPLASH_ACCESS_KEY') 
    url = f"https://api.unsplash.com/search/photos?page=1&query={topic}&client_id={access_key}"
    try:
        response = requests.get(url)
        response.raise_for_status() 
        data = response.json()
        if data['results']:
            image_url = data['results'][0]['urls']['regular'] 
            return image_url
        else:
            return ""  
    except Exception as e:
        print(f"Error fetching image from Unsplash: {e}")
        return ""


@app.route('/get_image', methods=['GET'])
def get_image():
    topic = request.args.get('topic')
    if not topic:
        return jsonify({'error': 'Missing topic parameter'}), 400
    image_url = get_topic_image(topic)
    return jsonify({'image_url': image_url})



@app.route('/get_topic', methods=['GET'])
def get_topic():
  topic = generate_random_topic()
  content, url = get_resources(topic)
  video_url = get_video_resource(topic)
  if content:
    summary = summarize_content(content)
  else:
    summary = "Could not find sufficient resources for the generated topic."
  return jsonify({
      'topic': topic,
      'summary': summary,
      'url': url,
      'video_url': video_url
    
  })

@app.route('/get_summary_audio', methods=['GET'])
def get_summary_audio():
    topic_summary = request.args.get('summary')
    if not topic_summary:
        return jsonify({'error': 'Missing summary parameter'}), 400
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=topic_summary,
        )
        audio_filename = "summary_audio.mp3"
        response.stream_to_file(os.path.join("static", audio_filename))
        return jsonify({'audio_url': url_for('static', filename=audio_filename)})
    except Exception as e:
        print(f"Error generating audio summary: {e}")
        return jsonify({'error': 'Failed to generate audio summary'}), 500



if __name__ == '__main__':
  app.run(debug=True)
