import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';

const UserPanelLayout = () => {
  const location = useLocation();
  
  const menuItems = [
    { path: '/account', label: 'Overview', icon: '📊' },
    { path: '/account/listings', label: 'My Listings', icon: '📝' },
    { path: '/account/messages', label: 'Messages', icon: '💬' },
    { path: '/account/profile', label: 'Profile', icon: '👤' },
  ];

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar (Desktop) */}
      <aside className="w-64 bg-white border-r hidden md:block">
        <div className="p-6">
          <h1 className="text-xl font-bold text-blue-600">My Panel</h1>
        </div>
        <nav className="mt-6">
          {menuItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center px-6 py-3 text-gray-700 hover:bg-blue-50 hover:text-blue-600 ${
                location.pathname === item.path ? 'bg-blue-50 text-blue-600 border-r-4 border-blue-600' : ''
              }`}
            >
              <span className="mr-3">{item.icon}</span>
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <div className="p-4 md:p-8">
          <Outlet />
        </div>
      </main>

      {/* Mobile Bottom Nav */}
      <nav className="md:hidden fixed bottom-0 w-full bg-white border-t flex justify-around p-3 z-50">
        {menuItems.map((item) => (
          <Link key={item.path} to={item.path} className="flex flex-col items-center text-xs text-gray-600">
            <span className="text-lg">{item.icon}</span>
            {item.label}
          </Link>
        ))}
      </nav>
    </div>
  );
};

export default UserPanelLayout;
