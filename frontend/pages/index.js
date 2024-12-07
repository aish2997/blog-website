import { useState, useEffect } from 'react';
import BlogCard from '../components/BlogCard';
import styles from '../styles/Home.module.css';

export default function Home() {
  const [blogs, setBlogs] = useState([]);
  const [search, setSearch] = useState('');

  // Fetch blog posts on initial load
  useEffect(() => {
    fetch('/api/blogs')
      .then((res) => res.json())
      .then((data) => setBlogs(data));
  }, []);

  // Filter blogs by title based on search input
  const filteredBlogs = blogs.filter(blog =>
    blog.title.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className={styles.container}>
      <h1>Welcome to My Technical Blog</h1>
      <input
        type="text"
        placeholder="Search blogs..."
        onChange={(e) => setSearch(e.target.value)}
        className={styles.searchBar}
      />
      <div className={styles.blogs}>
        {filteredBlogs.map((blog) => (
          <BlogCard key={blog.id} blog={blog} />
        ))}
      </div>
    </div>
  );
}
