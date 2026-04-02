// Предположим, это ваша страница создания поездки, например, CreateTripPage.tsx
import React, { useState } from 'react';
import { TripCreatedModal } from '../components/TripCreatedModal';

const CreateTripPage: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleCreateTrip = () => {
    // Здесь ваша логика создания поездки
    
    // После успешного создания поездки
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    // Здесь можно добавить переход на другую страницу или другие действия
  };

  return (
    <div>
      {/* Ваша форма создания поездки */}
      <button onClick={handleCreateTrip}>Создать поездку</button>
      
      {isModalOpen && <TripCreatedModal onClose={closeModal} />}
    </div>
  );
};

export default CreateTripPage;
