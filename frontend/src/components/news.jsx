import React, { useState, useEffect } from "react";

const news = () => {
  const [newsData, setNewsData] = useState(null);
  const apiUrl = "http://127.0.0.1:8000/";
  useEffect(() => {
    // Fetch data from the API
    fetch(apiUrl)
      .then((response) => response.json())
      .then((data) => setNewsData(data["News"]))
      .catch((error) => console.error("Error fetching data: ", error));
  }, []);

  return (
    <>
      <h1 style={{ textAlign: "center" }}>
        <span className="bold2">News Analysis Software</span>
      </h1>

      {newsData ? (
        <>
          <div>
            {newsData?.map((news) => (
              // <div>
              //   <p>{news["Categories"]}</p>
              //   <p>Title={news["Title"]}</p>
              //   <p>description={news["Description"].slice(0, 30) + '...'}</p>
              // </div>
              <div className="news-item">
                <p className="category">{news["Categories"]}</p>
                <p>
                  <span className="bold">Title: </span> {news["Title"]}
                </p>
                <p>
                  <span className="bold">Description: </span>{" "}
                  {news["Description"].slice(0, 30) + "..."}
                </p>
                <p>
                  Positivity{" "}
                  {100 -
                    Math.round(
                      parseFloat(news["Sentiment_Score"].split(" ")[1]) * 100
                    ) -
                    Math.round(
                      parseFloat(news["Sentiment_Score"].split(" ")[2]) * 100
                    )}
                </p>
                <p>
                  Neutrality{" "}
                  {Math.round(
                    parseFloat(news["Sentiment_Score"].split(" ")[2]) * 100
                  )}
                </p>
                <p>
                  Negativity{" "}
                  {Math.round(
                    parseFloat(news["Sentiment_Score"].split(" ")[1]) * 100
                  )}
                </p>
                <a className="bold4" target="_blank" href={news["URL"]}>
                  Read More
                </a>
                <hr className="divider" />
              </div>
            ))}
          </div>
        </>
      ) : (
        <>
          {/* <div>
            <h1>Latest Posts are Loading...</h1>
          </div> */}
          <h1>
            <span className="bold3">Latest Posts are loading...</span>
          </h1>
        </>
      )}
    </>
  );
};

export default news;