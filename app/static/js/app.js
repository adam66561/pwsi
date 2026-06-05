const API = '/api';
let token = localStorage.getItem('token');
let currentUser = JSON.parse(localStorage.getItem('user') || 'null');
let lastPayrollResult = null;
let lastPensionResult = null;
let lastPayrollInput = null;
let lastPensionInput = null;
const charts = {};

// ── Auth ──────────────────────────────────────────────
function showApp() {
    document.getElementById('loginPage').style.display = 'none';
    document.getElementById('mainNav').style.display = '';
    document.getElementById('appContent').style.display = '';
    document.getElementById('userInfo').textContent = `${currentUser.username} (${roleLabel(currentUser.role)})`;
    document.querySelectorAll('.admin-only').forEach(el => el.style.display = currentUser.role === 'admin' ? '' : 'none');
    document.querySelectorAll('.hr-only').forEach(el => el.style.display = (currentUser.role === 'hr_admin' || currentUser.role === 'admin') ? '' : 'none');
    navigateTo('dashboard');
}

function roleLabel(r) {
    return { user: 'Użytkownik', admin: 'Administrator', hr_admin: 'Kadry/Płace' }[r] || r;
}

function logout() {
    token = null; currentUser = null;
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    location.reload();
}

async function api(path, method = 'GET', body = null) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (token) opts.headers['Authorization'] = `Bearer ${token}`;
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(API + path, opts);
    if (res.status === 401) { logout(); return null; }
    if (path.endsWith('/pdf') || path.includes('/pdf')) {
        if (!res.ok) { const err = await res.json(); throw new Error(err.error || 'Błąd'); }
        return res.blob();
    }
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Błąd serwera');
    return data;
}

document.getElementById('loginForm').addEventListener('submit', async e => {
    e.preventDefault();
    const errEl = document.getElementById('loginError');
    errEl.classList.add('d-none');
    try {
        const data = await api('/auth/login', 'POST', {
            username: document.getElementById('loginUsername').value,
            password: document.getElementById('loginPassword').value,
        });
        token = data.access_token;
        currentUser = data.user;
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(currentUser));
        showApp();
    } catch (err) {
        errEl.textContent = err.message;
        errEl.classList.remove('d-none');
    }
});

document.getElementById('registerForm').addEventListener('submit', async e => {
    e.preventDefault();
    const errEl = document.getElementById('registerError');
    const okEl = document.getElementById('registerSuccess');
    errEl.classList.add('d-none'); okEl.classList.add('d-none');
    try {
        await api('/auth/register', 'POST', {
            username: document.getElementById('regUsername').value,
            email: document.getElementById('regEmail').value,
            password: document.getElementById('regPassword').value,
        });
        okEl.textContent = 'Konto utworzone! Możesz się zalogować.';
        okEl.classList.remove('d-none');
    } catch (err) {
        errEl.textContent = err.message;
        errEl.classList.remove('d-none');
    }
});

document.getElementById('logoutBtn').addEventListener('click', logout);

// ── Navigation ────────────────────────────────────────
function navigateTo(page) {
    document.querySelectorAll('.page').forEach(p => p.classList.add('d-none'));
    document.getElementById('page-' + page).classList.remove('d-none');
    document.querySelectorAll('[data-page]').forEach(a => {
        a.classList.toggle('active', a.dataset.page === page);
    });
    if (page === 'history') loadHistory();
    if (page === 'admin') loadAdmin();
    if (page === 'parameters') loadParameters();
    if (page === 'pension' && currentUser?.profile) fillPensionFromProfile();
}

document.querySelectorAll('[data-page]').forEach(a => {
    a.addEventListener('click', e => { e.preventDefault(); navigateTo(a.dataset.page); });
});

function fillPensionFromProfile() {
    const p = currentUser.profile;
    if (!p) return;
    if (p.age) document.getElementById('penAge').value = p.age;
    if (p.gender) document.getElementById('penGender').value = p.gender;
    if (p.planned_retirement_age) document.getElementById('penRetAge').value = p.planned_retirement_age;
    if (p.default_gross_salary) document.getElementById('penGross').value = p.default_gross_salary;
}

// ── Payroll ───────────────────────────────────────────
function getPayrollInput() {
    const mode = document.getElementById('payrollMode').value;
    const amount = parseFloat(document.getElementById('payrollAmount').value);
    return {
        mode, amount,
        contract_type: document.getElementById('payrollContract').value,
        ppk_enabled: document.getElementById('payrollPpk').checked,
        include_sickness: document.getElementById('payrollSickness').checked,
        custom_additions: parseFloat(document.getElementById('payrollAdditions').value) || 0,
        custom_deductions: parseFloat(document.getElementById('payrollDeductions').value) || 0,
    };
}

document.getElementById('calcPayrollBtn').addEventListener('click', async () => {
    const errEl = document.getElementById('payrollError');
    const resEl = document.getElementById('payrollResults');
    errEl.classList.add('d-none');
    const inp = getPayrollInput();
    if (!inp.amount || inp.amount <= 0) {
        errEl.textContent = 'Podaj poprawną kwotę (> 0)';
        errEl.classList.remove('d-none');
        return;
    }
    try {
        const endpoint = inp.mode === 'gross-from-net' ? '/calculator/gross-from-net' : '/calculator/net-from-gross';
        const key = inp.mode === 'gross-from-net' ? 'net' : 'gross';
        const result = await api(endpoint, 'POST', {
            [key]: inp.amount,
            contract_type: inp.contract_type,
            ppk_enabled: inp.ppk_enabled,
            include_sickness: inp.include_sickness,
            custom_additions: inp.custom_additions,
            custom_deductions: inp.custom_deductions,
        });
        lastPayrollResult = result;
        lastPayrollInput = inp;
        displayPayrollResult(result);
        resEl.classList.remove('d-none');
    } catch (err) {
        errEl.textContent = err.message;
        errEl.classList.remove('d-none');
    }
});

// function displayPayrollResult(r) {
//     document.getElementById('resGross').textContent = fmt(r.gross);
//     document.getElementById('resNet').textContent = fmt(r.net);
//     document.getElementById('resEmployer').textContent = fmt(r.total_employer_cost);

//     const rows = [
//         ['Składnik', 'Kwota (PLN)'],
//         ['Wynagrodzenie brutto', fmt(r.gross)],
//         ['ZUS pracownika', fmt(r.zus_employee)],
//         ['Składka zdrowotna', fmt(r.health)],
//         ['Podatek PIT', fmt(r.pit)],
//         ['PPK pracownika', fmt(r.ppk_employee)],
//         ['<strong>Wynagrodzenie netto</strong>', `<strong>${fmt(r.net)}</strong>`],
//         ['', ''],
//         ['ZUS pracodawcy', fmt(r.employer_zus)],
//         ['Fundusz Pracy', fmt(r.fp)],
//         ['FGŚP', fmt(r.fgszp)],
//         ['PPK pracodawcy', fmt(r.ppk_employer)],
//         ['<strong>Całkowity koszt pracodawcy</strong>', `<strong>${fmt(r.total_employer_cost)}</strong>`],
//     ];
//     document.getElementById('payrollTable').innerHTML = rows.map(([a, b]) =>
//         `<tr><td>${a}</td><td class="text-end">${b}</td></tr>`
//     ).join('');

//     renderChart('payrollChart', 'doughnut', {
//         labels: ['Netto', 'ZUS', 'Zdrowotna', 'PIT', 'PPK'],
//         data: [r.net, r.zus_employee, r.health, r.pit, r.ppk_employee],
//         colors: ['#28a745', '#dc3545', '#fd7e14', '#6f42c1', '#17a2b8'],
//     });
// }

function displayPayrollResult(r) {
    document.getElementById('resGross').textContent = fmt(r.gross);
    document.getElementById('resNet').textContent = fmt(r.net);
    document.getElementById('resEmployer').textContent = fmt(r.total_employer_cost);

    const d = r.details || {};

    const rows = [
        ['<strong>WYNAGRODZENIE BRUTTO:</strong>', `<strong>${fmt(r.gross)}</strong>`],

        ['EMERYTALNE:', fmt(d.zus_emerytalna)],
        ['RENTOWE:', fmt(d.zus_rentowa)],
        ['CHOROBOWE:', fmt(d.zus_chorobowa)],
        ['RAZEM SKŁADKI:', fmt(r.zus_employee)],
        ['BRUTTO MINUS SKŁADKI:', fmt(d.gross_minus_zus)],

        ['ZDROWOTNE (9%):', fmt(r.health)],
        ['ZDROWOTNE DO ODLICZENIA (7,75%):', fmt(d.health_deductible ?? 0)],

        ['KOSZTY UZYSKANIA PRZYCHODU:', fmt(d.kup)],
        ['PODSTAWA OPODATKOWANIA:', fmt(d.tax_basis_rounded ?? d.tax_basis)],

        ['PODATEK:', fmt(d.pit_before_rounding ?? r.pit)],
        ['ZALICZKA:', fmt(r.pit)],

        ['<strong>NETTO:</strong>', `<strong>${fmt(r.net)}</strong>`],

        ['', ''],

        ['<strong>DODATKOWE OBCIĄŻENIE PRACODAWCY</strong>', ''],

        ['EMERYTALNE:', fmt(d.employer_emerytalna)],
        ['RENTOWE:', fmt(d.employer_rentowa)],
        ['WYPADKOWE:', fmt(d.employer_wypadkowa)],
        ['FUNDUSZ PRACY:', fmt(d.fp_fs_total ?? r.fp)],
        ['FUNDUSZ GŚP:', fmt(r.fgszp)],

        ['RAZEM DODATKOWY KOSZT PRACODAWCY:', fmt(d.additional_employer_cost)],
        ['<strong>KOSZT CAŁKOWITY:</strong>', `<strong>${fmt(r.total_employer_cost)}</strong>`],
    ];

    document.getElementById('payrollTable').innerHTML = rows.map(([a, b]) =>
        `<tr><td>${a}</td><td class="text-end">${b}</td></tr>`
    ).join('');

    renderChart('payrollChart', 'doughnut', {
        labels: ['Netto', 'ZUS', 'Zdrowotna', 'PIT', 'PPK'],
        data: [r.net, r.zus_employee, r.health, r.pit, r.ppk_employee],
        colors: ['#28a745', '#dc3545', '#fd7e14', '#6f42c1', '#17a2b8'],
    });
}

document.getElementById('savePayrollBtn').addEventListener('click', async () => {
    if (!lastPayrollResult) { alert('Najpierw wykonaj kalkulację'); return; }
    const name = prompt('Nazwa wariantu:', 'Kalkulacja ' + new Date().toLocaleDateString('pl'));
    if (!name) return;
    try {
        await api('/calculator/save', 'POST', { name, type: 'payroll', input: lastPayrollInput, result: lastPayrollResult });
        alert('Zapisano!');
    } catch (err) { alert(err.message); }
});

// ── Pension ───────────────────────────────────────────
document.getElementById('penOfe').addEventListener('change', e => {
    document.getElementById('ofeFields').classList.toggle('d-none', !e.target.checked);
});

function getPensionInput() {
    return {
        current_age: parseInt(document.getElementById('penAge').value),
        gender: document.getElementById('penGender').value,
        retirement_age: parseInt(document.getElementById('penRetAge').value),
        gross_salary: parseFloat(document.getElementById('penGross').value),
        work_years: parseInt(document.getElementById('penWorkYears').value),
        zus_capital: parseFloat(document.getElementById('penZusCap').value),
        ofe_member: document.getElementById('penOfe').checked,
        ofe_capital: parseFloat(document.getElementById('penOfeCap').value) || 0,
        ofe_option: document.getElementById('penOfeOpt').value,
        ppk_enabled: document.getElementById('penPpk').checked,
        salary_growth: parseFloat(document.getElementById('penGrowth').value) / 100,
        inflation: parseFloat(document.getElementById('penInflation').value) / 100,
        planned_expenses: parseFloat(document.getElementById('penExpenses').value),
    };
}

document.getElementById('calcPensionBtn').addEventListener('click', async () => {
    const errEl = document.getElementById('pensionError');
    const resEl = document.getElementById('pensionResults');
    errEl.classList.add('d-none');
    const inp = getPensionInput();
    try {
        const result = await api('/pension/simulate', 'POST', inp);
        lastPensionResult = result;
        lastPensionInput = inp;
        displayPensionResult(result);
        resEl.classList.remove('d-none');
    } catch (err) {
        errEl.textContent = err.message;
        errEl.classList.remove('d-none');
    }
});

function displayPensionResult(r) {
    document.getElementById('penResZus').textContent = fmt(r.zus_monthly_pension);
    document.getElementById('penResOfe').textContent = fmt(r.ofe_monthly_pension);
    document.getElementById('penResPpk').textContent = fmt(r.ppk_monthly_pension);
    document.getElementById('penResTotal').textContent = fmt(r.total_monthly_pension);

    const cov = Math.min(r.expense_coverage || 0, 100);
    const bar = document.getElementById('penCoverage');
    bar.style.width = cov + '%';
    bar.textContent = cov.toFixed(0) + '%';
    bar.className = 'progress-bar ' + (cov >= 80 ? 'bg-success' : cov >= 50 ? 'bg-warning' : 'bg-danger');

    document.getElementById('penInflAdj').textContent = fmt(r.inflation_adjusted_pension) + ' PLN/mies.';

    const scenEl = document.getElementById('penScenarios');
    scenEl.innerHTML = Object.entries(r.scenarios || {}).map(([name, s]) =>
        `<div class="d-flex justify-content-between border-bottom py-2">
            <span class="text-capitalize"><strong>${name}</strong> (wiek: ${s.retirement_age})</span>
            <span>${fmt(s.total_monthly_pension)} PLN/mies.</span>
        </div>`
    ).join('') || '<p class="text-muted">Brak scenariuszy</p>';

    if (r.capital_growth?.length) {
        renderChart('pensionChart', 'line', {
            labels: r.capital_growth.map(c => 'Rok ' + c.year),
            datasets: [
                { label: 'ZUS', data: r.capital_growth.map(c => c.zus_capital), borderColor: '#1e3a5f', fill: false },
                { label: 'OFE', data: r.capital_growth.map(c => c.ofe_capital), borderColor: '#2e86ab', fill: false },
                { label: 'PPK', data: r.capital_growth.map(c => c.ppk_capital), borderColor: '#28a745', fill: false },
            ],
        });
    }
}

document.getElementById('savePensionBtn').addEventListener('click', async () => {
    if (!lastPensionResult) { alert('Najpierw wykonaj symulację'); return; }
    const name = prompt('Nazwa symulacji:', 'Emerytura ' + new Date().toLocaleDateString('pl'));
    if (!name) return;
    try {
        await api('/pension/save', 'POST', { name, input: lastPensionInput, result: lastPensionResult });
        alert('Zapisano!');
    } catch (err) { alert(err.message); }
});

// ── Reports ───────────────────────────────────────────
document.getElementById('repCompareBtn').addEventListener('click', async () => {
    const gross = parseFloat(document.getElementById('repCompareGross').value);
    try {
        const data = await api('/calculator/compare-contracts', 'POST', { gross });
        const labels = { uop: 'UoP', uz: 'UZ', uod: 'UoD' };
        document.getElementById('compareResults').innerHTML = data.comparisons.map(c =>
            `<div class="d-flex justify-content-between border-bottom py-2">
                <span><strong>${labels[c.contract_type]}</strong> — netto: ${fmt(c.net)}</span>
                <span class="text-muted">koszt prac.: ${fmt(c.total_employer_cost)}</span>
            </div>`
        ).join('');
        renderChart('compareChart', 'bar', {
            labels: data.comparisons.map(c => labels[c.contract_type]),
            datasets: [
                { label: 'Netto', data: data.comparisons.map(c => c.net), backgroundColor: '#28a745' },
                { label: 'Koszt pracodawcy', data: data.comparisons.map(c => c.total_employer_cost), backgroundColor: '#dc3545' },
            ],
        });
    } catch (err) { alert(err.message); }
});

document.getElementById('repAnnualBtn').addEventListener('click', async () => {
    const gross = parseFloat(document.getElementById('repAnnualGross').value);
    const growth = parseFloat(document.getElementById('repAnnualGrowth').value) / 100;
    try {
        const data = await api('/reports/annual', 'POST', { gross, months: 12*10, salary_growth: growth });
        document.getElementById('annualSummary').innerHTML =
            `<p><strong>Suma netto:</strong> ${fmt(data.summary.total_net)} PLN &nbsp;|&nbsp;
             <strong>Średnie netto:</strong> ${fmt(data.summary.avg_net)} PLN/mies.</p>`;
        renderChart('annualChart', 'line', {
            labels: data.forecast.map(m => 'M' + m.month),
            datasets: [
                { label: 'Brutto', data: data.forecast.map(m => m.gross), borderColor: '#1e3a5f', fill: false },
                { label: 'Netto', data: data.forecast.map(m => m.net), borderColor: '#28a745', fill: false },
            ],
        });
    } catch (err) { alert(err.message); }
});

async function downloadPdf(path, body, filename) {
    try {
        const blob = await api(path, 'POST', body);
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = filename; a.click();
        URL.revokeObjectURL(url);
    } catch (err) { alert(err.message); }
}

document.getElementById('exportPayrollPdf').addEventListener('click', () => {
    const gross = lastPayrollResult?.gross || parseFloat(document.getElementById('repCompareGross').value) || 8000;
    downloadPdf('/reports/payslip/pdf', { gross, contract_type: 'uop' }, 'raport_wynagrodzenia.pdf');
});

document.getElementById('exportPensionPdf').addEventListener('click', () => {
    const inp = lastPensionInput || getPensionInput();
    downloadPdf('/reports/pension/pdf', inp, 'prognoza_emerytury.pdf');
});

// ── History ───────────────────────────────────────────
async function loadHistory() {
    const type = document.getElementById('historyFilter').value;
    const path = '/calculator/history' + (type ? '?type=' + type : '');
    try {
        const items = await api(path);
        const el = document.getElementById('historyList');
        if (!items.length) { el.innerHTML = '<p class="text-muted">Brak zapisanych wariantów</p>'; return; }
        el.innerHTML = items.map(v => `
            <div class="col-md-6">
                <div class="card history-item p-3">
                    <div class="d-flex justify-content-between">
                        <strong>${v.name}</strong>
                        <span class="badge bg-${v.type === 'pension' ? 'info' : 'success'}">${v.type}</span>
                    </div>
                    <small class="text-muted">${new Date(v.created_at).toLocaleString('pl')}</small>
                    <pre class="mt-2 small bg-light p-2 rounded" style="max-height:120px;overflow:auto">${JSON.stringify(v.result, null, 2).substring(0, 300)}...</pre>
                </div>
            </div>`).join('');
    } catch (err) { console.error(err); }
}

document.getElementById('refreshHistory').addEventListener('click', loadHistory);
document.getElementById('historyFilter').addEventListener('change', loadHistory);

// ── Admin ─────────────────────────────────────────────
async function loadAdmin() {
    try {
        const users = await api('/admin/users');
        document.getElementById('adminUsersTable').innerHTML = `
            <table class="table table-sm">
                <thead><tr><th>ID</th><th>Login</th><th>Email</th><th>Rola</th><th>Status</th><th>Akcje</th></tr></thead>
                <tbody>${users.map(u => `<tr>
                    <td>${u.id}</td><td>${u.username}</td><td>${u.email}</td>
                    <td><select class="form-select form-select-sm" onchange="changeRole(${u.id}, this.value)">
                        <option value="user" ${u.role==='user'?'selected':''}>user</option>
                        <option value="admin" ${u.role==='admin'?'selected':''}>admin</option>
                        <option value="hr_admin" ${u.role==='hr_admin'?'selected':''}>hr_admin</option>
                    </select></td>
                    <td><span class="badge bg-${u.is_active?'success':'danger'}">${u.is_active?'Aktywny':'Nieaktywny'}</span></td>
                    <td>
                        <button class="btn btn-sm btn-outline-warning" onclick="resetPass(${u.id})">Reset hasła</button>
                        <button class="btn btn-sm btn-outline-secondary" onclick="toggleUser(${u.id})">Toggle</button>
                    </td>
                </tr>`).join('')}</tbody>
            </table>`;

        const logs = await api('/admin/audit-log');
        document.getElementById('auditLogTable').innerHTML = `
            <table class="table table-sm table-striped">
                <thead><tr><th>Data</th><th>User ID</th><th>Akcja</th><th>Szczegóły</th></tr></thead>
                <tbody>${logs.map(l => `<tr>
                    <td>${new Date(l.created_at).toLocaleString('pl')}</td>
                    <td>${l.user_id||'-'}</td><td>${l.action}</td><td>${l.details||''}</td>
                </tr>`).join('')}</tbody>
            </table>`;
    } catch (err) { console.error(err); }
}

async function changeRole(id, role) {
    try { await api(`/admin/users/${id}/role`, 'PUT', { role }); } catch (e) { alert(e.message); }
}
async function resetPass(id) {
    const pw = prompt('Nowe hasło:', 'reset123');
    if (!pw) return;
    try { await api(`/admin/users/${id}/reset`, 'POST', { password: pw }); alert('Zresetowano'); } catch (e) { alert(e.message); }
}
async function toggleUser(id) {
    try { await api(`/admin/users/${id}/toggle`, 'POST'); loadAdmin(); } catch (e) { alert(e.message); }
}

// ── Parameters ────────────────────────────────────────
async function loadParameters() {
    try {
        const params = await api('/admin/parameters');
        document.getElementById('parametersTable').innerHTML = `
            <table class="table">
                <thead><tr><th>Klucz</th><th>Opis</th><th>Wartość</th><th>Obowiązuje od</th><th>Akcja</th></tr></thead>
                <tbody>${params.map(p => `<tr>
                    <td><code>${p.key}</code></td><td>${p.description||''}</td>
                    <td><input type="number" class="form-control form-control-sm" id="param-${p.id}" value="${p.value}" step="0.0001" style="width:120px"></td>
                    <td>${p.valid_from}</td>
                    <td><button class="btn btn-sm btn-primary" onclick="saveParam(${p.id})">Zapisz</button></td>
                </tr>`).join('')}</tbody>
            </table>`;
    } catch (err) { console.error(err); }
}

async function saveParam(id) {
    const val = document.getElementById('param-' + id).value;
    if (!confirm('Potwierdź zmianę parametru?')) return;
    try {
        await api(`/admin/parameters/${id}`, 'PUT', { value: parseFloat(val) });
        alert('Parametr zaktualizowany');
        loadParameters();
    } catch (e) { alert(e.message); }
}

// ── Charts ────────────────────────────────────────────
function renderChart(canvasId, type, config) {
    if (charts[canvasId]) charts[canvasId].destroy();
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    let chartConfig;
    if (type === 'doughnut') {
        chartConfig = {
            type: 'doughnut',
            data: { labels: config.labels, datasets: [{ data: config.data, backgroundColor: config.colors }] },
            options: { responsive: true, plugins: { legend: { position: 'bottom' } } },
        };
    } else if (type === 'bar') {
        chartConfig = {
            type: 'bar',
            data: { labels: config.labels, datasets: config.datasets.map(d => ({ ...d, borderWidth: 1 })) },
            options: { responsive: true, plugins: { legend: { position: 'bottom' } } },
        };
    } else {
        chartConfig = {
            type: 'line',
            data: { labels: config.labels, datasets: config.datasets },
            options: { responsive: true, plugins: { legend: { position: 'bottom' } } },
        };
    }
    charts[canvasId] = new Chart(ctx, chartConfig);
}

function fmt(n) { return (n ?? 0).toLocaleString('pl-PL', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' PLN'; }

// ── Init ──────────────────────────────────────────────
if (token && currentUser) showApp();
