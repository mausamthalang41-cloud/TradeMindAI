import type { NewsArticle } from "../types";

type NewsListProps = {
  articles: NewsArticle[];
};

export default function NewsList({ articles }: NewsListProps) {
  if (articles.length === 0) {
    return null;
  }

  return (
    <div
      style={{
        marginTop: "30px",
        padding: "20px",
        background: "#334155",
        borderRadius: "15px",
      }}
    >
      <h2 style={{ textAlign: "center" }}>Recent News</h2>

      <div style={{ marginTop: "15px" }}>
        {articles.map((article) => (
          <a
            key={article.url}
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: "block",
              padding: "10px 0",
              borderBottom: "1px solid #475569",
              color: "white",
              textDecoration: "none",
            }}
          >
            <p style={{ margin: 0 }}>{article.headline}</p>
            <p
              style={{
                margin: "4px 0 0",
                fontSize: "12px",
                color: "#94a3b8",
              }}
            >
              {article.source} ·{" "}
              {new Date(article.datetime * 1000).toLocaleDateString()}
            </p>
          </a>
        ))}
      </div>
    </div>
  );
}
