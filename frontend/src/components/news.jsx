import React, { useState, useEffect } from "react";

const news = () => {
  const [newsData, setNewsData] = useState([]);
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
      {newsData?.length > 0 ? (
        <>
          <div>
            {newsData?.map((news) => (
              <div>
                <p>{news["Categories"]}</p>
                <p>Title={news["Title"]}</p>
                <p>description={news["Description"].slice(0, 30) + '...'}</p>
              </div>
            ))}
          </div>
        </>
      ) : (
        <>
          <div>
            Latest Posts are Loading...
          </div>
        </>
      )}
    </>
  );
};

export default news;