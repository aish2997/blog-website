import { useState, useEffect } from 'react';

const CommentSection = ({ blogId }) => {
  const [comments, setComments] = useState([]);
  const [comment, setComment] = useState('');

  useEffect(() => {
    fetch(`/api/comments?blogId=${blogId}`)
      .then((res) => res.json())
      .then((data) => setComments(data));
  }, [blogId]);

  const handleCommentSubmit = async (e) => {
    e.preventDefault();
    if (!comment) return;

    const newComment = { blogId, text: comment };

    await fetch('/api/comments', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(newComment),
    });

    setComments([...comments, newComment]);
    setComment('');
  };

  return (
    <div>
      <h3>Comments</h3>
      <form onSubmit={handleCommentSubmit}>
        <textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Add a comment"
        />
        <button type="submit">Post Comment</button>
      </form>
      <div>
        {comments.map((comment, index) => (
          <div key={index}>{comment.text}</div>
        ))}
      </div>
    </div>
  );
};

export default CommentSection;
