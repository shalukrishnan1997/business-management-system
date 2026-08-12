import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { getApiErrorMessage } from "@/api/client";
import { createResource, listResource, updateResource } from "@/api/resource";
import { Button } from "@/components/ui/Button";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { FieldError, FieldLabel, TextInput, TextSelect } from "@/components/ui/Field";
import { Modal } from "@/components/ui/Modal";
import { PageHeader } from "@/components/ui/PageHeader";
import { Pagination } from "@/components/ui/Pagination";
import { SearchField } from "@/components/ui/SearchField";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { usePaginatedList } from "@/hooks/usePaginatedList";
import { formatMoney } from "@/utils/format";

type Employee = {
  id: number;
  employee_code: string;
  first_name: string;
  last_name: string;
  full_name: string;
  email: string;
  phone: string;
  department: number;
  designation: number;
  department_name?: string;
  designation_name?: string;
  employment_type: string;
  basic_salary: string;
  status: string;
};

type Department = { id: number; name: string; status: string };
type Designation = {
  id: number;
  name: string;
  department: number;
  department_name?: string;
  status: string;
};

const emptyEmp = {
  first_name: "",
  last_name: "",
  email: "",
  phone: "",
  department: "",
  designation: "",
  employment_type: "full_time",
  basic_salary: "0",
  status: "active",
};

export function EmployeesPage() {
  const qc = useQueryClient();
  const list = usePaginatedList<Employee>("employees", "/employees/");
  const departmentsQuery = useQuery({
    queryKey: ["departments", "options"],
    queryFn: () =>
      listResource<Department>("/departments/", { page_size: 100, status: "active" }),
  });
  const designationsQuery = useQuery({
    queryKey: ["designations", "options"],
    queryFn: () =>
      listResource<Designation>("/designations/", { page_size: 100, status: "active" }),
  });

  const [empOpen, setEmpOpen] = useState(false);
  const [deptOpen, setDeptOpen] = useState(false);
  const [desOpen, setDesOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState(emptyEmp);
  const [deptName, setDeptName] = useState("");
  const [desForm, setDesForm] = useState({ name: "", department: "" });
  const [error, setError] = useState<string | null>(null);

  const filteredDesignations = useMemo(() => {
    const all = designationsQuery.data?.results ?? [];
    if (!form.department) return all;
    return all.filter((d) => String(d.department) === form.department);
  }, [designationsQuery.data, form.department]);

  const saveEmp = useMutation({
    mutationFn: () => {
      const body = {
        first_name: form.first_name,
        last_name: form.last_name,
        email: form.email,
        phone: form.phone,
        department: Number(form.department),
        designation: Number(form.designation),
        employment_type: form.employment_type,
        basic_salary: form.basic_salary,
        status: form.status,
      };
      if (editingId) return updateResource<Employee>(`/employees/${editingId}/`, body);
      return createResource<Employee>("/employees/", body);
    },
    onSuccess: async () => {
      setEmpOpen(false);
      await qc.invalidateQueries({ queryKey: ["employees"] });
    },
    onError: (err) => setError(getApiErrorMessage(err)),
  });

  const saveDept = useMutation({
    mutationFn: () => createResource<Department>("/departments/", { name: deptName }),
    onSuccess: async () => {
      setDeptOpen(false);
      setDeptName("");
      await qc.invalidateQueries({ queryKey: ["departments"] });
    },
  });

  const saveDes = useMutation({
    mutationFn: () =>
      createResource<Designation>("/designations/", {
        name: desForm.name,
        department: Number(desForm.department),
      }),
    onSuccess: async () => {
      setDesOpen(false);
      setDesForm({ name: "", department: "" });
      await qc.invalidateQueries({ queryKey: ["designations"] });
    },
  });

  const columns: Column<Employee>[] = [
    {
      key: "code",
      header: "Code",
      render: (r) => <span className="font-medium">{r.employee_code}</span>,
    },
    {
      key: "name",
      header: "Name",
      render: (r) => (
        <div>
          <p className="font-medium">{r.full_name}</p>
          <p className="text-xs text-muted">{r.email || r.phone || "—"}</p>
        </div>
      ),
    },
    {
      key: "org",
      header: "Org",
      render: (r) => (
        <span>
          {r.department_name} · {r.designation_name}
        </span>
      ),
    },
    { key: "salary", header: "Salary", render: (r) => formatMoney(r.basic_salary) },
    { key: "status", header: "Status", render: (r) => <StatusBadge value={r.status} /> },
    {
      key: "actions",
      header: "",
      render: (r) => (
        <Button
          variant="ghost"
          onClick={() => {
            setEditingId(r.id);
            setForm({
              first_name: r.first_name,
              last_name: r.last_name || "",
              email: r.email || "",
              phone: r.phone || "",
              department: String(r.department),
              designation: String(r.designation),
              employment_type: r.employment_type,
              basic_salary: r.basic_salary,
              status: r.status,
            });
            setError(null);
            setEmpOpen(true);
          }}
        >
          Edit
        </Button>
      ),
    },
  ];

  return (
    <section>
      <PageHeader title="Employees" description="Departments, designations, and roster.">
        <Button variant="secondary" onClick={() => setDeptOpen(true)}>
          Add department
        </Button>
        <Button
          variant="secondary"
          onClick={() => {
            setDesForm({ name: "", department: "" });
            setDesOpen(true);
          }}
        >
          Add designation
        </Button>
        <Button
          onClick={() => {
            setEditingId(null);
            setForm(emptyEmp);
            setError(null);
            setEmpOpen(true);
          }}
        >
          Add employee
        </Button>
      </PageHeader>
      <div className="mb-4">
        <SearchField value={list.search} onChange={list.setSearch} placeholder="Search employees…" />
      </div>
      <DataTable columns={columns} rows={list.rows} rowKey={(r) => r.id} loading={list.isLoading} />
      <Pagination page={list.page} pageSize={20} total={list.total} onPageChange={list.setPage} />

      <Modal
        open={empOpen}
        title={editingId ? "Edit employee" : "Add employee"}
        onClose={() => setEmpOpen(false)}
        footer={
          <>
            <Button variant="secondary" onClick={() => setEmpOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => saveEmp.mutate()}
              disabled={
                !form.first_name ||
                !form.department ||
                !form.designation ||
                saveEmp.isPending
              }
            >
              Save
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <FieldLabel>First name</FieldLabel>
              <TextInput
                value={form.first_name}
                onChange={(e) => setForm((f) => ({ ...f, first_name: e.target.value }))}
              />
            </div>
            <div>
              <FieldLabel>Last name</FieldLabel>
              <TextInput
                value={form.last_name}
                onChange={(e) => setForm((f) => ({ ...f, last_name: e.target.value }))}
              />
            </div>
          </div>
          <div>
            <FieldLabel>Email</FieldLabel>
            <TextInput
              value={form.email}
              onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
            />
          </div>
          <div>
            <FieldLabel>Phone</FieldLabel>
            <TextInput
              value={form.phone}
              onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
            />
          </div>
          <div>
            <FieldLabel>Department</FieldLabel>
            <TextSelect
              value={form.department}
              onChange={(e) =>
                setForm((f) => ({ ...f, department: e.target.value, designation: "" }))
              }
            >
              <option value="">Select…</option>
              {(departmentsQuery.data?.results ?? []).map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </TextSelect>
          </div>
          <div>
            <FieldLabel>Designation</FieldLabel>
            <TextSelect
              value={form.designation}
              onChange={(e) => setForm((f) => ({ ...f, designation: e.target.value }))}
            >
              <option value="">Select…</option>
              {filteredDesignations.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </TextSelect>
          </div>
          <div>
            <FieldLabel>Employment type</FieldLabel>
            <TextSelect
              value={form.employment_type}
              onChange={(e) => setForm((f) => ({ ...f, employment_type: e.target.value }))}
            >
              {["full_time", "part_time", "contract", "intern"].map((t) => (
                <option key={t} value={t}>
                  {t.replaceAll("_", " ")}
                </option>
              ))}
            </TextSelect>
          </div>
          <div>
            <FieldLabel>Basic salary</FieldLabel>
            <TextInput
              value={form.basic_salary}
              onChange={(e) => setForm((f) => ({ ...f, basic_salary: e.target.value }))}
            />
          </div>
          <FieldError message={error || undefined} />
        </div>
      </Modal>

      <Modal
        open={deptOpen}
        title="Add department"
        onClose={() => setDeptOpen(false)}
        footer={
          <>
            <Button variant="secondary" onClick={() => setDeptOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => saveDept.mutate()}
              disabled={!deptName.trim() || saveDept.isPending}
            >
              Save
            </Button>
          </>
        }
      >
        <FieldLabel>Name</FieldLabel>
        <TextInput value={deptName} onChange={(e) => setDeptName(e.target.value)} />
      </Modal>

      <Modal
        open={desOpen}
        title="Add designation"
        onClose={() => setDesOpen(false)}
        footer={
          <>
            <Button variant="secondary" onClick={() => setDesOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => saveDes.mutate()}
              disabled={!desForm.name.trim() || !desForm.department || saveDes.isPending}
            >
              Save
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <FieldLabel>Department</FieldLabel>
            <TextSelect
              value={desForm.department}
              onChange={(e) => setDesForm((f) => ({ ...f, department: e.target.value }))}
            >
              <option value="">Select…</option>
              {(departmentsQuery.data?.results ?? []).map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </TextSelect>
          </div>
          <div>
            <FieldLabel>Name</FieldLabel>
            <TextInput
              value={desForm.name}
              onChange={(e) => setDesForm((f) => ({ ...f, name: e.target.value }))}
            />
          </div>
        </div>
      </Modal>
    </section>
  );
}
