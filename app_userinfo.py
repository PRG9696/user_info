import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# --- Page Configuration ---
st.set_page_config(
    page_title="GitHub User & Commit Insight Tool",
    page_icon="🐙",
    layout="wide"
)

st.title("🐙 GitHub User Info & Commit Analytics")
st.markdown("Inspect profile metrics, repository statistics, and recent commit trends.")

# --- Sidebar Inputs & Token Resolution ---
st.sidebar.header("Configuration")
username = st.sidebar.text_input("GitHub Username", value="torvalds")

# Check Streamlit secrets first, otherwise fallback to sidebar input
secrets_token = st.secrets.get("GITHUB_TOKEN", "") if hasattr(st, "secrets") else ""
github_token = st.sidebar.text_input(
    "GitHub Access Token (Optional)", 
    value=secrets_token,
    type="password", 
    help="Add a token to increase API rate limit from 60 to 5,000 requests per hour."
)

# Request Headers setup
headers = {}
if github_token:
    headers["Authorization"] = f"bearer {github_token}"

# --- API Helper Functions ---
@st.cache_data(ttl=600)
def get_github_user(user_handle):
    """Fetch user profile information."""
    url = f"https://api.github.com/users/{user_handle}"
    res = requests.get(url, headers=headers)
    return res.json(), res.status_code

@st.cache_data(ttl=600)
def get_github_repos(user_handle):
    """Fetch public repositories for the user."""
    url = f"https://api.github.com/users/{user_handle}/repos?per_page=100&sort=updated"
    res = requests.get(url, headers=headers)
    return res.json(), res.status_code

@st.cache_data(ttl=600)
def get_repo_commits(user_handle, repo_name):
    """Fetch up to 100 recent commits for a given repository."""
    url = f"https://api.github.com/repos/{user_handle}/{repo_name}/commits?per_page=100"
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        commits = res.json()
        commit_dates = [c['commit']['committer']['date'] for c in commits if isinstance(c, dict) and 'commit' in c]
        return commit_dates
    return []

# --- Main App Logic ---
if username:
    user_data, user_status = get_github_user(username)
    
    if user_status == 404:
        st.error(f"User **{username}** not found. Please check the spelling.")
    elif user_status != 200:
        st.error(f"API Error ({user_status}): {user_data.get('message', 'Failed to retrieve data.')}")
    else:
        # 1. Profile Header Layout
        col_avatar, col_info = st.columns([1, 3])
        
        with col_avatar:
            st.image(user_data.get("avatar_url"), width=180)
            st.markdown(f"**[{user_data.get('login')}]({user_data.get('html_url')})**")
            
        with col_info:
            st.subheader(user_data.get("name") or username)
            if user_data.get("bio"):
                st.caption(user_data.get("bio"))
                
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Public Repos", user_data.get("public_repos", 0))
            c2.metric("Followers", user_data.get("followers", 0))
            c3.metric("Following", user_data.get("following", 0))
            c4.metric("Public Gists", user_data.get("public_gists", 0))
            
            st.write(f"📍 **Location:** {user_data.get('location') or 'Not specified'}")
            st.write(f"🏢 **Company:** {user_data.get('company') or 'Not specified'}")

        st.divider()

        # 2. Repositories & Visualizations
        repos_data, repos_status = get_github_repos(username)
        
        if repos_status == 200 and repos_data:
            df_repos = pd.DataFrame(repos_data)
            cols = ["name", "stargazers_count", "forks_count", "language", "html_url", "updated_at"]
            df_display = df_repos[[c for c in cols if c in df_repos.columns]].copy()

            # Repository Charts
            st.subheader("📊 Repository Overview")
            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                if "language" in df_display.columns:
                    lang_counts = df_display["language"].fillna("Unknown").value_counts().reset_index()
                    lang_counts.columns = ["Language", "Count"]
                    fig_lang = px.pie(
                        lang_counts, 
                        values="Count", 
                        names="Language", 
                        title="Primary Languages Distribution",
                        hole=0.4
                    )
                    st.plotly_chart(fig_lang, use_container_width=True)

            with chart_col2:
                if "stargazers_count" in df_display.columns:
                    top_starred = df_display.sort_values(by="stargazers_count", ascending=False).head(8)
                    fig_stars = px.bar(
                        top_starred, 
                        x="stargazers_count", 
                        y="name", 
                        orientation="h",
                        title="Top Repositories by Stars",
                        labels={"stargazers_count": "Stars", "name": "Repository"},
                        color="stargazers_count",
                        color_continuous_scale="Blues"
                    )
                    fig_stars.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_stars, use_container_width=True)

            # 3. Commit History Analytics Section
            st.subheader("📈 Commit Activity Timeline")
            
            repo_names = df_display["name"].tolist()
            selected_repo = st.selectbox("Select a repository to inspect recent commits:", repo_names)
            
            if selected_repo:
                commit_dates = get_repo_commits(username, selected_repo)
                
                if commit_dates:
                    # Convert to DataFrame
                    df_commits = pd.DataFrame({"commit_time": pd.to_datetime(commit_dates)})
                    df_commits["Date"] = df_commits["commit_time"].dt.date
                    
                    # Group commits by date
                    commit_counts = df_commits.groupby("Date").size().reset_index(name="Commit Count")
                    
                    # Commit Timeline Chart
                    fig_commits = px.line(
                        commit_counts, 
                        x="Date", 
                        y="Commit Count",
                        title=f"Recent Commit Activity for '{selected_repo}'",
                        markers=True
                    )
                    fig_commits.update_traces(line_color="#2da44e")
                    st.plotly_chart(fig_commits, use_container_width=True)
                else:
                    st.info("No commit history found or repository is empty/unreachable.")

            # 4. Interactive Data Table
            st.subheader("📁 Public Repositories Data")
            df_display_table = df_display.rename(columns={
                "name": "Repository Name",
                "stargazers_count": "Stars",
                "forks_count": "Forks",
                "language": "Language",
                "html_url": "URL",
                "updated_at": "Last Updated"
            })

            st.dataframe(
                df_display_table,
                column_config={"URL": st.column_config.LinkColumn("GitHub Link")},
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No public repositories found for this user.")