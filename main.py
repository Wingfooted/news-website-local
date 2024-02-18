from flask import Flask, render_template, session, redirect, url_for, request
import base64
import os
import hashlib
import ast
import time

def hash_string(input_string):
    # Using SHA-256 hash function
    sha256_hash = hashlib.sha256(input_string.encode()).hexdigest()

    # Truncate to 8 characters
    truncated_hash = sha256_hash[:8].replace("/", "g")

    return truncated_hash

def get_articles(hash_list):
    output = []
    color_dict = {
        'Literature': '#FF5733',
        'Analysis': '#024f9c',
        'Foreign Policy': '#33FF57',
        'Agriculture': '#029c5c',
        'Opinion': '#9c021c'
    }

    for article_hash in [a.replace("\n", "") for a in hash_list]:
        element = {}
        element["hash"] = article_hash
        with open(f"static/metad/{article_hash}.txt") as file:
            metadata = file.readlines()
            element["summary"] = metadata[0]
            element["category"] = metadata[1]
            element["title"] = metadata[2]
            element["author"] = metadata[3]
            element["color"] = color_dict[metadata[1].replace("\n", "")]

        output.append(element)
    return output

    '''<!--meta.write(summary + '\n')
            meta.write(category + '\n')
            meta.write(title + '\n')
            meta.write(author)-->'''



app = Flask(__name__)
app.secret_key = "VGTYJKNIJ3MS77O@J#MSOIK4MDK53F2JISD<FNM86KSAANGGB5F0NMA1MKFUHNAM"

@app.route("/", methods=["GET", "POST"])
def index():
    with open("static/display.txt", "r") as file:
        preferances=file.readlines()
        for line in preferances:
            line_list = line.split(",")
            if line_list[0] == "LATEST":
                latest_hash = line_list[1:]
            elif line_list[0] == "FEATURED":
                featured_hash = line_list[1:]
            elif line_list[0] == "CAROUSEL":
                carousel_hash = line_list[1:]
            elif line_list[0] == "LARGE":
                large_hash = line_list[1:]
            
    return render_template(
        "main.html" 
        , latest=get_articles(latest_hash)
        , feature=get_articles(featured_hash)
        , carousel=get_articles(carousel_hash)
        , large=get_articles(large_hash)[0]
    )

@app.route("/a/<article>")
def article(article):
    #rendering the article
    article_hash = hash_string(article)
    print(article_hash)
    files = os.listdir('static/articles')
    if f"{article_hash}.txt" in files:
        #try:
        with open(f"static/articles/{article_hash}.txt", 'r') as article:
            content = [ast.literal_eval(line) for line in article.readlines()]
        with open(f"static/metad/{article_hash}.txt", 'r') as article:
            md = article.readlines()

            '''meta.write(summary + '\n')
                    meta.write(category + '\n')
                    meta.write(title + '\n')
                    meta.write(author)'''
            if md[3] == "Alexander Wells":
                md.append("Alexander Wells is a University of Sydney Student studying a Bachelors in Agricultural Science and Mathematics. A burgenoning Contributor to L'Anthropologie, he explores a variety of fields and a growing interest in agricultural journalism.")
            elif md[3] == "Daniel Tran":
                md.append("Daniel Tran, an aspiring student at the University of Sydney, is currently pursuing a dual degree in Engineering and Science. Hailing from the Tran Family Farm Estate, which constitutes 1.34% of all farmland in NSW, Daniel developed a profound affinity for farming. Beyond academics, Daniel's notable strength is evident, showcasing an impressive ability to lift weights of up to 200kg.")
            return render_template("article.html", content=content, metadata=md, hash=article_hash)
        #except:
        #    return 
        #finally:
        #    time.sleep(5)
        #    return redirect(url_for("index"))
    else: 
        return redirect(url_for("index"))

@app.route("/c/<category>")
def category(category):
    return render_template("category.html")

@app.route("/editor", methods=["GET", "POST"])
def editor():
    
    if request.method == "GET":
        if not 'user' in session:
            return redirect(url_for('login'))

    elif request.method == "POST":
        if not 'user' in session:
            return redirect(url_for('login'))
        
        author = request.form['author']
        category = request.form["category"]
        title = request.form.get("title")
        summary = request.form.get("summary")

        article_hash = hash_string(title)
        #thumbnail
        thumbnail = request.files["thumbnail"] if "thumbnail" in request.files else None
        if thumbnail:
            thumbnail.save(os.path.join('static/images', f"{article_hash}.png"))

        content = []

        form = ast.literal_eval(request.form["form-data"])
        img_count = 1
        for id_element in form:
            #all element id's follow the format where it is first name, then the UID
            element_content = request.form.get(id_element)
            element_type = id_element.split("-")[0]
            if element_content or element_type== "img":
                if element_type == "text":
                    content.append(("t", element_content))
                elif element_type == "sub":
                    content.append(("s", element_content))
                elif element_type == "quote":
                    content.append(("q", element_content))
                elif element_type == "img":
                    if id_element in request.files:
                        img = request.files[id_element]
                        if img:
                            img.save(os.path.join('static/articleimages', f"{article_hash}_{img_count}.png"))
                            content.append(("i",os.path.join('/static/articleimages', f"{article_hash}_{img_count}.png")))
                            img_count+=1
                            
        #write the article file
        if article_hash == hash_string(""):
            #no article title
            return redirect(url_for("editor"))
        elif f"{article_hash}.t xt" in os.listdir('static/articles'):
            #article title allready exists
            return redirect(url_for("editor"))
        else:
            #article can be created
            with open(f"static/articles/{article_hash}.txt", "w") as article:
                for line in content:
                    article.write(str(line) + '\n')
            
            with open(f"static/metad/{article_hash}.txt", "w") as meta:
                meta.write(summary + '\n')
                meta.write(category + '\n')
                meta.write(title + '\n')
                meta.write(author)
        
        return redirect(url_for('article', article=title, _external=True))

    return render_template('editor.html', author=session['user'])     

@app.route("/login", methods=["GET", "POST"])
def login():
    
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username and password:
            with open("static/usernames.txt", "r") as file:
                for line in file.readlines():
                    if username == line.split(",")[0] and password == line.split(",")[1]:
                        session["user"] = line.split(",")[2]
                        return redirect(url_for("index"))

    elif request.method == "GET":
        pass
    
    return render_template("login.html")

@app.route("/maintenance")
def maintenance():
    return "Hello"


if __name__ == "__main__":
    app.run(debug=True, port=8000)

