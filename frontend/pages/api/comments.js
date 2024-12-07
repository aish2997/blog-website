export default async function handler(req, res) {
    if (req.method === 'GET') {
      const { blogId } = req.query;
      const response = await fetch(`http://127.0.0.1:8000/comments?blogId=${blogId}`);
      const comments = await response.json();
      return res.status(200).json(comments);
    }
  
    if (req.method === 'POST') {
      const newComment = req.body;
      const response = await fetch('http://127.0.0.1:8000/comments', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newComment),
      });
      const createdComment = await response.json();
      return res.status(201).json(createdComment);
    }
  
    res.status(405).end();
  }
  