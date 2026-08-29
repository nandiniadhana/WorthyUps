
  (function () {
    // 1. Try both possible localStorage keys
    let raw = localStorage.getItem("studentData") || localStorage.getItem("studentDashboard");

    let data = null;
    if (raw) {
      try {
        data = JSON.parse(raw);
      } catch (e) {
        console.error("Failed to parse stored student data:", e);
        data = null;
      }
    }

    // 2. If no data exists, show the empty state and stop
    if (!data) {
      const emptyState = document.getElementById("emptyState");
      if (emptyState) {
        emptyState.classList.remove("hidden");
      }
      return;
    }

    // 3. Handle nested JSON shapes safely: data.data, data.body, data.student, or data itself
    const student = data.data || data.body || data.student || data;

    // 4. Auto-detect fields with fallback chains, render if elements exist
    const fullName =
      student.full_name ||
      student.name ||
      student.student_name ||
      "N/A";

    const email =
      student.email ||
      student.student_email ||
      "No email provided";

    const major =
      student.major ||
      student.course ||
      student.department ||
      "N/A";

    const phone =
      student.phone ||
      student.phone_number ||
      "N/A";

    const fieldMap = {
      studentName: fullName,
      studentEmail: email,
      studentMajor: major,
      studentPhone: phone,
    };

    let renderedAny = false;

    Object.keys(fieldMap).forEach(function (elementId) {
      const el = document.getElementById(elementId);
      if (el) {
        el.textContent = fieldMap[elementId];
        renderedAny = true;
      }
    });

    // If no matching elements found in the DOM, render a dynamic card instead
    if (!renderedAny) {
      const container = document.getElementById("dashboardContent") || document.body;
      const card = document.createElement("div");
      card.className = "p-6 rounded-lg shadow-md bg-white border border-gray-200 space-y-2";
      card.innerHTML =
        '<p><strong>Name:</strong> ' + fullName + '</p>' +
        '<p><strong>Email:</strong> ' + email + '</p>' +
        '<p><strong>Major:</strong> ' + major + '</p>' +
        '<p><strong>Phone:</strong> ' + phone + '</p>';
      container.appendChild(card);
    }
  })();