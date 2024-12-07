import styles from '../styles/BlogPost.module.css';

const BlogPost = ({ blog }) => (
  <div className={styles.blogPost}>
    <h1>{blog.title}</h1>
    <div dangerouslySetInnerHTML={{ __html: blog.content }} />
  </div>
);

export default BlogPost;
