import Link from 'next/link';
import styles from '../styles/Home.module.css';

const BlogCard = ({ blog }) => (
  <div className={styles.card}>
    <h2>{blog.title}</h2>
    <p>{blog.excerpt}</p>
    <Link href={`/blog/${blog.id}`}>
      <a className={styles.readMore}>Read More</a>
    </Link>
  </div>
);

export default BlogCard;
