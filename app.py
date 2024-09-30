import nest_asyncio
from typing import Optional

import streamlit as st
from duckduckgo_search import DDGS
from phi.tools.newspaper4k import Newspaper4k

import openai
import os 

from dotenv import load_dotenv
load_dotenv()

os.getenv("OPENAI_API_KEY")


nest_asyncio.apply()

st.set_page_config(
    page_title="News Articles",
    page_icon=":orange_heart:",
)

st.title("News Articles powered by OpenAI")

st.markdown("##### :orange_heart: built using OpenAI's API")

openai.api_key = os.getenv("OPENAI_API_KEY")


def truncate_text(text: str, words: int) -> str:
    return " ".join(text.split()[:words])


def main() -> None:
    # Get models
    summary_model = st.sidebar.selectbox(
        "Select Summary Model", options=["llama3-8b-8192", "mixtral-8x7b-32768", "llama3-70b-8192"]
    )
    writer_model = st.sidebar.selectbox(
        "Select Writer Model", options=["llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768"]
    )

    # Checkboxes for research options
    st.sidebar.markdown("## Research Options")

    num_search_results = st.sidebar.slider(
        ":sparkles: Number of Search Results",
        min_value=3,
        max_value=20,
        value=7,
        help="Number of results to search for, note only the articles that can be read will be summarized.",
    )

    per_article_summary_length = st.sidebar.slider(
        ":sparkles: Length of Article Summaries",
        min_value=100,
        max_value=2000,
        value=800,
        step=100,
        help="Number of words per article summary",
    )
    news_summary_length = st.sidebar.slider(
        ":sparkles: Length of Draft",
        min_value=1000,
        max_value=10000,
        value=5000,
        step=100,
        help="Number of words in the draft article, this should fit the context length of the model.",
    )

    # Get topic for report
    article_topic = st.text_input(
        ":spiral_calendar_pad: Enter a topic",
        value="AI and its impact on society",
    )
    write_article = st.button("Write Article")
    if write_article:
        news_results = []
        news_summary: Optional[str] = None
        with st.status("Reading News", expanded=False) as status:
            with st.container():
                news_container = st.empty()
                ddgs = DDGS()
                newspaper_tools = Newspaper4k()
                results = ddgs.news(keywords=article_topic, max_results=num_search_results)
                for r in results:
                    if "url" in r:
                        article_data = newspaper_tools.get_article_data(r["url"])
                        if article_data and "text" in article_data:
                            r["text"] = article_data["text"]
                            news_results.append(r)
                            if news_results:
                                news_container.write(news_results)
            if news_results:
                news_container.write(news_results)
            status.update(label="News Search Complete", state="complete", expanded=False)












        if len(news_results) > 0:
            news_summary = ""
            with st.status("Summarizing News", expanded=False) as status:
                with st.container():
                    summary_container = st.empty()
                    for news_result in news_results:
                        news_summary += f"### {news_result['title']}\n\n"
                        news_summary += f"- Date: {news_result['date']}\n\n"
                        news_summary += f"- URL: {news_result['url']}\n\n"
                        news_summary += f"#### Introduction\n\n{news_result['body']}\n\n"

                        # Use OpenAI API to generate summary
                        response = openai.ChatCompletion.create(
                            model="gpt-3.5-turbo",
                            messages=[{"role": "system", "content": "Summarize the article."}],
                            max_tokens=per_article_summary_length,
                            temperature=0.7,
                            stop=["\n\n", "<|endoftext|>"],
                        )
                        print(response.choices[0])
                        _summary = response.choices[0].get('text', '').strip()
                        
                        _summary_length = len(_summary.split())
                        if _summary_length > news_summary_length:
                            _summary = truncate_text(_summary, news_summary_length)
                        news_summary += "#### Summary\n\n"
                        news_summary += _summary
                        news_summary += "\n\n---\n\n"
                        if news_summary:
                            summary_container.markdown(news_summary)
                        if len(news_summary.split()) > news_summary_length:
                            break


                if news_summary:
                    summary_container.markdown(news_summary)
                status.update(label="News Summarization Complete", state="complete", expanded=False)

        if news_summary is None:
            st.write("Sorry could not find any news or web search results. Please try again.")
            return
        







        

        article_draft = ""
        article_draft += f"# Topic: {article_topic}\n\n"
        if news_summary:
            article_draft += "## Summary of News Articles\n\n"
            article_draft += f"This section provides a summary of the news articles about {article_topic}.\n\n"
            article_draft += "<news_summary>\n\n"
            article_draft += f"{news_summary}\n\n"
            article_draft += "</news_summary>\n\n"

        with st.status("Writing Draft", expanded=True) as status:
            with st.container():
                draft_container = st.empty()
                draft_container.markdown(article_draft)
            status.update(label="Draft Complete", state="complete", expanded=False)

        with st.spinner("Writing Article..."):
            final_report = ""
            final_report_container = st.empty()
            # Use OpenAI API to generate the article
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "Write the article."}],
                max_tokens=2000,
                temperature=0.7,
                stop=["\n\n", "<|endoftext|>"],
            )

            print(response.choices[0])
            if hasattr(response.choices[0], 'text'):
                final_report = response.choices[0].text.strip()
            elif hasattr(response.choices[0], 'content'):
                final_report = response.choices[0].content.strip()
            else:
                final_report = str(response.choices[0]).strip()

    st.sidebar.markdown("---")
    if st.sidebar.button("Restart"):
        st.rerun()


main()



