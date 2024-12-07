export default async function handler(req, res) {
    const response = await fetch('http://127.0.0.1:8000/blogs');
    const blogs = await response.json();
    res.status(200).json(blogs);
  }
  