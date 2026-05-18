import { useEffect, useState } from "react";
import "./App.css";

const AUTH_API = "http://127.0.0.1:8000/api/auth";
const DIGEST_API = "http://127.0.0.1:8000/api/digest";

export default function App() {
  const [mode, setMode] = useState("login");

  const [token, setToken] = useState(
    sessionStorage.getItem("token")
  );

  const [user, setUser] = useState(null);

  const [loading, setLoading] =
    useState(false);

  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
  });

  async function register() {
    try {
      setLoading(true);

      const res = await fetch(
        `${AUTH_API}/register`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify({
            name: form.name,
            email: form.email,
            password: form.password,
          }),
        }
      );

      const data = await res.json();

      if (res.ok) {
        alert("Account created");

        setMode("login");

        setForm({
          name: "",
          email: "",
          password: "",
        });
      } else {
        alert(
          data.detail ||
            "Registration failed"
        );
      }
    } catch (err) {
      console.error(err);
      alert("Server error");
    } finally {
      setLoading(false);
    }
  }

  async function login() {
    try {
      setLoading(true);

      const formData =
        new URLSearchParams();

      formData.append(
        "username",
        form.email
      );

      formData.append(
        "password",
        form.password
      );

      const res = await fetch(
        `${AUTH_API}/login`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/x-www-form-urlencoded",
          },
          body: formData,
        }
      );

      const data = await res.json();

      if (
        res.ok &&
        data.access_token
      ) {
        sessionStorage.setItem(
          "token",
          data.access_token
        );

        setToken(data.access_token);

        await fetchMe(
          data.access_token
        );
      } else {
        alert(
          data.detail ||
            "Login failed"
        );
      }
    } catch (err) {
      console.error(err);
      alert("Server error");
    } finally {
      setLoading(false);
    }
  }

  async function fetchMe(
    authToken = token
  ) {
    try {
      const res = await fetch(
        `${AUTH_API}/me`,
        {
          headers: {
            Authorization: `Bearer ${authToken}`,
          },
        }
      );

      const data = await res.json();

      if (res.ok) {
        setUser(data);
      } else {
        logout();
      }
    } catch (err) {
      console.error(err);
      logout();
    }
  }

  async function sendDigest() {
    try {
      setLoading(true);

      const res = await fetch(
        `${DIGEST_API}/send-now`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const data = await res.json();

      if (res.ok) {
        alert(
          "Digest email sent successfully"
        );
      } else {
        alert(
          data.detail ||
            "Failed to send digest"
        );
      }
    } catch (err) {
      console.error(err);
      alert("Server error");
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    sessionStorage.removeItem("token");

    setToken(null);
    setUser(null);
    setTopArticles([]);
  }

  useEffect(() => {
    if (token) {
      fetchMe(token);
    }
  }, [token]);

  /* =========================
     AUTH PAGE
  ========================= */

  if (!token || !user) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          background:
            "linear-gradient(135deg,#faf7f2,#ffffff,#f8f5ef)",
        }}
      >
        {/* LEFT SIDE */}

        <div
          style={{
            flex: 1,
            padding: "80px",
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
          }}
        >
          <div
            style={{
              display: "inline-block",
              padding:
                "10px 18px",
              borderRadius: 999,
              background:
                "rgba(255,255,255,0.7)",
              border:
                "1px solid rgba(0,0,0,0.06)",
              width: "fit-content",
              marginBottom: 28,
              fontWeight: 700,
              color: "#111827",
              backdropFilter:
                "blur(12px)",
            }}
          >
            AI DIGEST
          </div>

          <h1
            style={{
              fontSize: 68,
              lineHeight: 1.05,
              maxWidth: 700,
              margin: 0,
              color: "#111827",
              letterSpacing:
                "-0.05em",
              fontWeight: 800,
            }}
          >
            Premium AI News
            Intelligence Platform
          </h1>

          <p
            style={{
              marginTop: 28,
              maxWidth: 600,
              fontSize: 19,
              lineHeight: 1.8,
              color: "#6b7280",
            }}
          >
            Personalized AI
            insights curated from
            OpenAI, Anthropic,
            ArXiv, Reddit,
            YouTube and more —
            designed for modern AI
            professionals.
          </p>

          <div
            style={{
              display: "flex",
              gap: 22,
              marginTop: 42,
            }}
          >
            {[
              {
                title: "6+",
                desc: "AI Sources",
              },
              {
                title: "24/7",
                desc: "Monitoring",
              },
              {
                title: "Smart",
                desc: "Personalization",
              },
            ].map((item) => (
              <div
                key={item.title}
                style={{
                  background:
                    "rgba(255,255,255,0.75)",
                  border:
                    "1px solid rgba(0,0,0,0.06)",
                  borderRadius: 28,
                  padding:
                    "26px 32px",
                  minWidth: 170,
                  backdropFilter:
                    "blur(18px)",
                  boxShadow:
                    "0 10px 30px rgba(0,0,0,0.04)",
                }}
              >
                <h2
                  style={{
                    margin: 0,
                    fontSize: 34,
                    color:
                      "#111827",
                  }}
                >
                  {item.title}
                </h2>

                <p
                  style={{
                    marginTop: 10,
                    color:
                      "#6b7280",
                  }}
                >
                  {item.desc}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* RIGHT SIDE */}

        <div
          style={{
            width: 520,
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            padding: 40,
          }}
        >
          <div
            style={{
              width: "100%",
              background:
                "rgba(255,255,255,0.82)",
              border:
                "1px solid rgba(255,255,255,0.9)",
              backdropFilter:
                "blur(24px)",
              borderRadius: 34,
              padding: 42,
              boxShadow:
                "0 20px 60px rgba(0,0,0,0.08)",
            }}
          >
            <h2
              style={{
                fontSize: 34,
                margin: 0,
                color: "#111827",
              }}
            >
              {mode === "login"
                ? "Welcome Back"
                : "Create Account"}
            </h2>

            <p
              style={{
                color: "#6b7280",
                marginTop: 14,
                marginBottom: 34,
                lineHeight: 1.7,
              }}
            >
              Access your
              personalized AI
              intelligence dashboard
            </p>

            {mode ===
              "register" && (
              <input
                type="text"
                placeholder="Full Name"
                value={form.name}
                onChange={(e) =>
                  setForm({
                    ...form,
                    name:
                      e.target
                        .value,
                  })
                }
                style={inputStyle}
              />
            )}

            <input
              type="email"
              placeholder="Email Address"
              value={form.email}
              onChange={(e) =>
                setForm({
                  ...form,
                  email:
                    e.target.value,
                })
              }
              style={inputStyle}
            />

            <input
              type="password"
              placeholder="Password"
              value={form.password}
              onChange={(e) =>
                setForm({
                  ...form,
                  password:
                    e.target.value,
                })
              }
              style={inputStyle}
            />

            <button
              onClick={
                mode === "login"
                  ? login
                  : register
              }
              disabled={loading}
              style={{
                width: "100%",
                padding: 18,
                marginTop: 10,
                borderRadius: 18,
                border: "none",
                background:
                  "#111827",
                color: "#fff",
                fontSize: 16,
                fontWeight: 700,
                cursor: "pointer",
                boxShadow:
                  "0 12px 30px rgba(17,24,39,0.18)",
              }}
            >
              {loading
                ? "Please wait..."
                : mode === "login"
                ? "Login"
                : "Create Account"}
            </button>

            <p
              style={{
                marginTop: 28,
                textAlign: "center",
                color: "#6b7280",
              }}
            >
              {mode === "login"
                ? "Don't have an account?"
                : "Already have an account?"}

              <span
                onClick={() =>
                  setMode(
                    mode ===
                      "login"
                      ? "register"
                      : "login"
                  )
                }
                style={{
                  color:
                    "#111827",
                  fontWeight: 700,
                  cursor: "pointer",
                }}
              >
                {mode === "login"
                  ? " Register"
                  : " Login"}
              </span>
            </p>
          </div>
        </div>
      </div>
    );
  }

  /* =========================
     DASHBOARD
  ========================= */

  return (
    <div
      style={{
        minHeight: "100vh",
        background:
          "linear-gradient(180deg,#faf7f2,#f9fafb)",
        padding: 36,
      }}
    >
      <div
        style={{
          maxWidth: 1450,
          margin: "0 auto",
        }}
      >
        {/* TOPBAR */}

        <div
          style={{
            display: "flex",
            justifyContent:
              "space-between",
            alignItems: "center",
            marginBottom: 34,
          }}
        >
          <div>
            <h1
              style={{
                margin: 0,
                fontSize: 42,
                color: "#111827",
              }}
            >
              AI Digest
            </h1>

            <p
              style={{
                color: "#6b7280",
                marginTop: 10,
              }}
            >
              Personalized AI
              intelligence dashboard
            </p>
          </div>

          <button
            onClick={logout}
            style={{
              padding:
                "14px 24px",
              borderRadius: 16,
              border: "none",
              background:
                "#111827",
              color: "#fff",
              fontWeight: 700,
              cursor: "pointer",
            }}
          >
            Logout
          </button>
        </div>

        {/* GRID */}

        <div
          style={{
            display: "grid",
            gridTemplateColumns:
              "1.4fr 1fr",
            gap: 28,
          }}
        >
          {/* LEFT */}

          <div>
            <div
              style={{
                background:
                  "rgba(255,255,255,0.85)",
                borderRadius: 34,
                padding: 42,
                backdropFilter:
                  "blur(20px)",
                border:
                  "1px solid rgba(255,255,255,0.9)",
                boxShadow:
                  "0 20px 50px rgba(0,0,0,0.05)",
              }}
            >
              <h2
                style={{
                  margin: 0,
                  fontSize: 36,
                  color:
                    "#111827",
                }}
              >
                Welcome back,
                {user.name ||
                  " User"}
              </h2>

              <p
                style={{
                  marginTop: 16,
                  color:
                    "#6b7280",
                  lineHeight: 1.8,
                  maxWidth: 650,
                }}
              >
                Generate your latest
                personalized AI
                digest and stay
                updated with the most
                important AI news,
                research and
                breakthroughs.
              </p>

              <button
                onClick={sendDigest}
                disabled={loading}
                style={{
                  marginTop: 30,
                  padding:
                    "18px 28px",
                  borderRadius: 18,
                  border: "none",
                  background:
                    "#111827",
                  color: "#fff",
                  fontWeight: 700,
                  fontSize: 16,
                  cursor: "pointer",
                  boxShadow:
                    "0 14px 30px rgba(17,24,39,0.15)",
                }}
              >
                {loading
                  ? "Sending..."
                  : "Send AI Digest"}
              </button>
            </div>

            {/* STATS */}

            <div
              style={{
                display: "grid",
                gridTemplateColumns:
                  "repeat(3,1fr)",
                gap: 22,
                marginTop: 24,
              }}
            >
              {[
                {
                  title: "6+",
                  desc: "AI Sources",
                },
                {
                  title: "24/7",
                  desc: "Monitoring",
                },
                {
                  title: "Smart",
                  desc: "Personalization",
                },
              ].map((item) => (
                <div
                  key={item.title}
                  style={{
                    background:
                      "rgba(255,255,255,0.85)",
                    borderRadius: 28,
                    padding:
                      "30px",
                    border:
                      "1px solid rgba(255,255,255,0.9)",
                    backdropFilter:
                      "blur(16px)",
                    boxShadow:
                      "0 12px 34px rgba(0,0,0,0.04)",
                  }}
                >
                  <h2
                    style={{
                      margin: 0,
                      fontSize: 34,fontWeight: 350,
                      color: "#111827",
                      letterSpacing: "-0.04em",
                    }}
                  >
                    {item.title}
                  </h2>

                  <p
                    style={{
                      marginTop: 10,
                      color:
                        "#6b7280",
                    }}
                  >
                    {item.desc}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* RIGHT */}

          <div
            style={{
              background:
                "rgba(255,255,255,0.85)",
              borderRadius: 34,
              padding: 36,
              border:
                "1px solid rgba(255,255,255,0.9)",
              backdropFilter:
                "blur(20px)",
              boxShadow:
                "0 20px 50px rgba(0,0,0,0.05)",
              height: "fit-content",
            }}
          >
            <h2
              style={{
                color: "#111827",
                fontWeight: 500,
                margin: 0,
                fontSize: 28,
              }}
            >
              User Profile

            </h2>

            <div
              style={{
                marginTop: 30,
              }}
            >
              <ProfileRow
                label="Email"
                value={user.email}
              />

              <ProfileRow
                label="Status"
                value={
                  user.is_verified
                    ? "Verified"
                    : "Not Verified"
                }
              />

              <ProfileRow
                label="Delivery"
                value="Email Digest"
              />

              <div
  style={{
    padding: "18px 0",
    borderBottom:
      "1px solid rgba(0,0,0,0.06)",
  }}
>
  <p
    style={{
      color: "#4b5563",
      marginBottom: 14,
      fontSize: 14,
      fontWeight: 700,
    }}
  >
    Sources
  </p>

  <div
    style={{
      display: "flex",
      flexWrap: "wrap",
      gap: 12,
    }}
  >
    {[
      {
        name: "OpenAI",
        desc:
          "GPT updates, research & announcements",
      },
      {
        name: "Anthropic",
        desc:
          "Claude research and safety updates",
      },
      {
        name: "Reddit",
        desc:
          "AI community discussions & trends",
      },
      {
        name: "YouTube",
        desc:
          "AI videos and creator insights",
      },
      {
        name: "ArXiv",
        desc:
          "Latest AI research papers",
      },
      {
        name: "TechCrunch",
        desc:
          "AI startup and tech news",
      },
    ].map((source) => (
      <div
        key={source.name}
        onClick={() =>
          alert(source.desc)
        }
        style={{
          padding: "12px 16px",
          borderRadius: 16,
          background:
            "rgba(255,255,255,0.9)",
          border:
            "1px solid rgba(0,0,0,0.06)",
          cursor: "pointer",
          transition:
            "all 0.22s ease",
          boxShadow:
            "0 4px 14px rgba(0,0,0,0.04)",
          fontWeight: 700,
          color: "#111827",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform =
            "translateY(-2px)";
          e.currentTarget.style.boxShadow =
            "0 12px 24px rgba(0,0,0,0.08)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform =
            "translateY(0)";
          e.currentTarget.style.boxShadow =
            "0 4px 14px rgba(0,0,0,0.04)";
        }}
      >
        {source.name}
      </div>
    ))}
  </div>
</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* COMPONENT */

function ProfileRow({
  label,
  value,
}) {
  return (
    <div
      style={{
        padding: "18px 0",
        borderBottom:
          "1px solid rgba(0,0,0,0.06)",
      }}
    >
      <p
        style={{
          color: "#9ca3af",
          marginBottom: 8,
          fontSize: 14,
        }}
      >
        {label}
      </p>

      <h3
        style={{
          margin: 0,
          color: "#111827",
          fontSize: 17,
        }}
      >
        {value}
      </h3>
    </div>
  );
}

/* INPUT STYLE */

const inputStyle = {
  width: "100%",
  padding: "16px 18px",
  marginBottom: 18,
  borderRadius: 16,
  border: "1px solid rgba(0,0,0,0.08)",
  background: "rgba(255,255,255,0.9)",
  fontSize: 15,
  outline: "none",
  color: "#111827",
  boxSizing: "border-box",
};