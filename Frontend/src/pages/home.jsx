import { useState } from "react";
import User from "../assets/user.png";
import Add from "../assets/add.png";
import Delete from "../assets/delete.png";

const Home = () => {
  const [tasks, setTasks] = useState([]);
  const [inputValue, setInputValue] = useState("");

  const addTask = () => {
    if (inputValue.trim() === "") return;

    const newTask = {
      id: Date.now(),
      title: inputValue,
      completed: false,
      createdAt: new Date().toLocaleDateString(),
    };

    setTasks([...tasks, newTask]);
    setInputValue("");
  };

  const deleteTask = (id) => {
    setTasks(tasks.filter((task) => task.id !== id));
  };

  const toggleComplete = (id) => {
    setTasks(
      tasks.map((task) =>
        task.id === id ? { ...task, completed: !task.completed } : task
      )
    );
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      addTask();
    }
  };

  const completedCount = tasks.filter((task) => task.completed).length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-8 bg-white rounded-lg shadow-md p-4">
        <h1 className="text-3xl font-bold text-indigo-600">My To-Do List</h1>
        <img src={User} alt="User" className="w-12 h-12 rounded-full" />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-gray-600 text-sm">Total Tasks</p>
          <p className="text-2xl font-bold text-indigo-600">{tasks.length}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-gray-600 text-sm">Completed</p>
          <p className="text-2xl font-bold text-green-600">{completedCount}</p>
        </div>
      </div>

      {/* Input Field */}
      <div className="flex gap-2 mb-6">
        <input
          type="text"
          placeholder="Add a new task..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <button
          onClick={addTask}
          className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg px-6 py-3 flex items-center gap-2 transition"
        >
          <img src={Add} alt="Add" className="w-5 h-5" />
          Add
        </button>
      </div>

      {/* Task List */}
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        {tasks.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-gray-500 text-lg">No tasks yet. Add one to get started!</p>
          </div>
        ) : (
          <ul className="divide-y">
            {tasks.map((task) => (
              <li
                key={task.id}
                className="p-4 hover:bg-gray-50 transition flex items-center justify-between"
              >
                <div className="flex items-center gap-4 flex-1">
                  <input
                    type="checkbox"
                    checked={task.completed}
                    onChange={() => toggleComplete(task.id)}
                    className="w-5 h-5 text-indigo-600 rounded cursor-pointer"
                  />
                  <div className="flex-1">
                    <p
                      className={`text-lg ${
                        task.completed
                          ? "text-gray-400 line-through"
                          : "text-gray-800"
                      }`}
                    >
                      {task.title}
                    </p>
                    <p className="text-xs text-gray-500">{task.createdAt}</p>
                  </div>
                </div>
                <button
                  onClick={() => deleteTask(task.id)}
                  className="bg-red-500 hover:bg-red-600 text-white rounded p-2 transition"
                >
                  <img src={Delete} alt="Delete" className="w-5 h-5" />
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default Home;
