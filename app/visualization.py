import matplotlib.pyplot as plt
from wordcloud import WordCloud


def v(text: str, filename: str):
    wc = WordCloud(width=300, height=300, background_color="white").generate(text)
    plt.axis("off")
    plt.imshow(wc, interpolation="bilinear")
    plt.savefig(filename)
