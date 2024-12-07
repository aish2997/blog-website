import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import BlogPost from '../../components/BlogPost';
import CommentSection from '../../components/CommentSection';
import styles from '../../styles/BlogPost.module.css';

export default function Blog() {
  const router = useRouter();
  const { id } = router.query;
  const [blog, setBlog] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      fetch(`/api/blogs/${id}`)
        .then((res) => res.json())
        .then((data) => {
          setBlog(data);
          setLoading(false);
        });
    }
  }, [id]);

  if (loading) return <div>Loading...</div>;

  return (
    <div className={styles.container}>
      <BlogPost blog={blog} />
      <CommentSection blogId={id} />
    </div>
  );
}
